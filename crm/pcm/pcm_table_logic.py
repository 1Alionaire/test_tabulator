from .models import PcmSample, PcmSampleTimeTableRecord
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
import django.utils

# NIOSH 7400 constants
FIELD_AREA_MM2 = Decimal('0.00785')           # Walton-Beckett graticule field area, mm²
FILTER_COLLECTION_AREA_MM2 = Decimal('385')   # effective collection area of 25-mm filter, mm²

PCM_ENTRY_FIELDS = {'client_sample', 'iwa_owa', 'location', 'time_in', 'time_out',
                    'flow_rate_before', 'flow_rate_after', 'sample_volume'}

PCM_ANALYSIS_FIELDS = {'amount_fibers', 'fields', 'qc_amount_fibers', 'qc_fields'}

# always calculated on the server, values from the client are ignored
PCM_RESULT_FIELDS = {'fiber_per_mm', 'fiber_per_cub_cm', 'qc_fiber_per_mm', 'qc_fiber_per_cub_cm'}


def _round(value, places):
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)

def sampling_minutes(sample):
    if sample.time_in is None or sample.time_out is None:
        return None
    minutes_in = sample.time_in.hour * 60 + sample.time_in.minute
    minutes_out = sample.time_out.hour * 60 + sample.time_out.minute
    return (minutes_out - minutes_in) % (24 * 60)   # sampling past midnight

def average_flow_rate(sample):
    if sample.flow_rate_before is None or sample.flow_rate_after is None:
        return None
    return (sample.flow_rate_before + sample.flow_rate_after) / 2

def calculate_sample_volume(sample):
    # liters = average flow rate (L/min) * sampling time (min)
    minutes = sampling_minutes(sample)
    flow_rate = average_flow_rate(sample)
    if minutes is None or flow_rate is None:
        return None
    return _round(flow_rate * minutes, '0.01')

def calculate_fiber_results(amount_fibers, fields, sample_volume):
    # returns (fibers/mm², fibers/cc), without blank correction
    if amount_fibers is None or not fields:
        return None, None
    fiber_density = amount_fibers / (fields * FIELD_AREA_MM2)
    if not sample_volume:
        return _round(fiber_density, '0.01'), None
    fiber_concentration = fiber_density * FILTER_COLLECTION_AREA_MM2 / (sample_volume * 1000)
    return _round(fiber_density, '0.01'), _round(fiber_concentration, '0.001')

def calculate_sample_results(sample):
    # volume typed by hand is kept until time in/out and both flow rates are filled
    calculated_volume = calculate_sample_volume(sample)
    if calculated_volume is not None:
        sample.sample_volume = calculated_volume

    sample.fiber_per_mm, sample.fiber_per_cub_cm = calculate_fiber_results(
        sample.amount_fibers, sample.fields, sample.sample_volume)
    sample.qc_fiber_per_mm, sample.qc_fiber_per_cub_cm = calculate_fiber_results(
        sample.qc_amount_fibers, sample.qc_fields, sample.sample_volume)

def set_sample_fields(sample, row, field_names):
    for name in field_names & row.keys():
        field = PcmSample._meta.get_field(name)
        value = row[name]
        if value == '':
            value = None
        # Tabulator sends null for cleared cells; NOT NULL columns fall back to their model default
        if value is None and not field.null:
            value = field.get_default()
        try:
            setattr(sample, name, field.to_python(value))
        except ValidationError as e:
            raise ValidationError(f'{sample.lab_sample} {name}: {" ".join(e.messages)}')

def validate_sample(sample):
    try:
        sample.full_clean(exclude=['pcm_project'])
    except ValidationError as e:
        details = '; '.join(f'{name}: {" ".join(messages)}' for name, messages in e.message_dict.items())
        raise ValidationError(f'{sample.lab_sample} {details}')


class PCMSamplesDataEntryManager():
    def __init__(self, pcm_project, input_data):
        self.pcm_project = pcm_project
        self.rows = input_data.get('rows', [])
        self.data_to_delete = input_data.get('deleted', [])

    def validate_whole_object(self):
        row_ids = [int(row['id']) for row in self.rows if row.get('id')]
        if len(row_ids) != len(set(row_ids)):
            return {'error': 'duplicate sample ids'}

        if set(row_ids) & {int(sample_id) for sample_id in self.data_to_delete}:
            return {'error': 'sample cannot be updated and deleted at the same time'}

    def table_update_processing(self) -> dict:
        result = {'status': 'ok'}
        with transaction.atomic():
            samples = {sample.id : sample for sample in
                        PcmSample.objects.select_for_update().filter(pcm_project=self.pcm_project)}

            delete_ids = {int(sample_id) for sample_id in self.data_to_delete}
            update_ids = {int(row['id']) for row in self.rows if row.get('id')}
            missing = (delete_ids | update_ids) - samples.keys()
            if missing:
                raise ValidationError(f'samples not found (deleted?): {sorted(missing)}')

            result['deleted'] = self._delete_data(delete_ids)
            result['updated'], result['created'] = self._save_rows(samples)
        return result

    def _delete_data(self, delete_ids):
        if not delete_ids:
            return 0
        deleted, _ = PcmSample.objects.filter(pcm_project=self.pcm_project, pk__in=delete_ids).delete()
        return deleted

    def _save_rows(self, samples):
        lab_id = self.pcm_project.project.lab_id
        now = timezone.now()
        to_update = []
        to_create = []

        # table order defines row numbers and lab sample ids
        for position, row in enumerate(self.rows, start=1):
            if row.get('id'):
                sample = samples[int(row['id'])]
                sample.time_update = now
                to_update.append(sample)
            else:
                sample = PcmSample(pcm_project=self.pcm_project)
                to_create.append(sample)

            sample.row_number = position
            sample.lab_sample = f'{lab_id}-{position}'
            set_sample_fields(sample, row, PCM_ENTRY_FIELDS)
            calculate_sample_results(sample)
            validate_sample(sample)

        PcmSample.objects.bulk_update(
            to_update, sorted(PCM_ENTRY_FIELDS | PCM_RESULT_FIELDS | {'row_number', 'lab_sample', 'time_update'})
        )
        PcmSample.objects.bulk_create(to_create)
        return len(to_update), len(to_create)


class PCMSamplesAnalysisManager():
    def __init__(self, pcm_project, input_data):
        self.pcm_project = pcm_project
        self.rows = input_data.get('rows', [])

    def validate_whole_object(self):
        if any(not row.get('id') for row in self.rows):
            return {'error': 'sample id is required'}

    def table_update_processing(self) -> dict:
        result = {'status': 'ok'}
        with transaction.atomic():
            update_ids = {int(row['id']) for row in self.rows}
            samples = {sample.id : sample for sample in
                        PcmSample.objects.select_for_update().filter(pcm_project=self.pcm_project, pk__in=update_ids)}

            missing = update_ids - samples.keys()
            if missing:
                raise ValidationError(f'samples not found (deleted?): {sorted(missing)}')

            now = timezone.now()
            for row in self.rows:
                sample = samples[int(row['id'])]
                set_sample_fields(sample, row, PCM_ANALYSIS_FIELDS)
                calculate_sample_results(sample)
                validate_sample(sample)
                sample.time_update = now

            result['updated'] = PcmSample.objects.bulk_update(
                samples.values(), sorted(PCM_ANALYSIS_FIELDS | PCM_RESULT_FIELDS | {'sample_volume', 'time_update'})
            )
        return result

class PCMTimeTableManager():
    def __init__(self, input_data, year, month, day, user):
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])
        self.year = year
        self.month = month
        self.day = day
        self.user = user

    def table_update_processing(self) -> dict:
        result = {'status': 'ok'}
        with transaction.atomic():
            if self.data_to_update:
                result['updated'] = self._update_data()
            if self.data_to_create:
                result['created'] = self._create_data()
        return result

    def _update_data(self):
        work_data = self.data_to_update
        id_list = [element.get('id') for element in work_data]

        records_for_update = {record.id : record for record in 
                                            PcmSampleTimeTableRecord.objects.select_for_update().filter(pk__in=id_list)}

        for record_row in work_data:
            sample = records_for_update[int(record_row.get('id'))]
            setattr(sample, 'project', record_row['project'])
            setattr(sample, 'start_time', record_row['start_time'])
            setattr(sample, 'end_time', record_row['end_time'])
            setattr(sample, 'row_number', record_row['row_number'])
            sample.time_update = django.utils.timezone.now()

        updated = PcmSampleTimeTableRecord.objects.bulk_update(
                                records_for_update.values(), sorted({'time_update', 'project', 'start_time', 'row_number', 'end_time'})
                            )

        return updated

    def _create_data(self):
        time_table_array = []
        data = self.data_to_create
        for record in data:
            time_table_array.append(PcmSampleTimeTableRecord(
                analyst = self.user,
                year = self.year,
                month = self.month,
                day = self.day,
                start_time = record['start_time'], 
                end_time = record['end_time'], 
                row_number = record['row_number'], 
                project = record['project'], 
            ))

        for record in time_table_array:
            record.full_clean()
            record.save()

        return len(time_table_array)

def validate_pcm_project_for_report(pcm_project):
    errors = []
    fields = {'analyst' : 'No analyst',
            'date_collect' : 'No date collect',
            'date_analyze':'No date analysis', 
            'work_area': 'No work area',
            'technician': 'No technician',
            'rotometer':'No rotometer',
            'type_sampling' : 'No type sampling'}

    for field, text_error in fields.items():
        if getattr(pcm_project, field) == None or getattr(pcm_project, field) == '':
            errors.append(text_error)

    return errors