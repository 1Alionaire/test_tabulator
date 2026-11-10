import math
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from pcm.models import PcmProject, PcmSample, SampleQCAcceptOrReject
from api.v1.utils import check_versions

PCM_ENTRY_FIELDS = {'client_sample', 'iwa_owa', 'location', 'time_in', 'time_out',
                    'flow_rate_before', 'flow_rate_after', 'sample_volume', 'segment_area'}

PCM_ANALYSIS_FIELDS = {'amount_fibers', 'fields', 'qc_amount_fibers', 'qc_fields', 'segment_area'}

# always calculated on the server, values from the client are ignored
PCM_RESULT_FIELDS = {'fiber_per_mm', 'fiber_per_cub_cm', 'qc_fiber_per_mm', 'qc_fiber_per_cub_cm',
                     'qc_accept_or_reject'}


def _round(value, places):
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def sampling_minutes(sample):
    if sample.time_in is None or sample.time_out is None:
        return None
    minutes_in = sample.time_in.hour * 60 + sample.time_in.minute
    minutes_out = sample.time_out.hour * 60 + sample.time_out.minute
    return (minutes_out - minutes_in) % (24 * 60)  # sampling past midnight


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


def calculate_fiber_results(amount_fibers, fields, sample_volume, segment_area):
    if (amount_fibers is None) or (fields is None) or (sample_volume is None) or (segment_area is None):
        return None, None

    fiber_density = ((amount_fibers / fields) / segment_area)
    fiber_concentration = ((amount_fibers / fields) * 49) / sample_volume

    return _round(fiber_density, '0.01'), _round(fiber_concentration, '0.001')

def calculate_sample_results(sample):
    # volume typed by hand is kept until time in/out and both flow rates are filled
    calculated_volume = calculate_sample_volume(sample)
    if calculated_volume is not None:
        sample.sample_volume = calculated_volume

    sample.fiber_per_mm, sample.fiber_per_cub_cm = calculate_fiber_results(
        sample.amount_fibers, sample.fields, sample.sample_volume, sample.segment_area)

    sample.qc_fiber_per_mm, sample.qc_fiber_per_cub_cm = calculate_fiber_results(
        sample.qc_amount_fibers, sample.qc_fields, sample.sample_volume, sample.segment_area)

def calculate_qc_accept_or_reject(fiber_per_mm, qc_fiber_per_mm, sr):
    # |√X₁ − √X₂| <= 2.77 × ((√X₁ + √X₂) / 2) × Sr -> Accept, otherwise Reject
    # X₁ = original F/mm², X₂ = QC F/mm²; no QC count or no Sr (empty or 0) -> no verdict
    if fiber_per_mm is None or not qc_fiber_per_mm or not sr:
        return None
    # float math in the same order as qcUpdateResult in pcm_qc.js, so browser and server agree
    sqrt_original = math.sqrt(float(fiber_per_mm))
    sqrt_qc = math.sqrt(float(qc_fiber_per_mm))
    limit = 2.77 * ((sqrt_original + sqrt_qc) / 2) * float(sr)
    if abs(sqrt_original - sqrt_qc) <= limit:
        return SampleQCAcceptOrReject.Accept
    return SampleQCAcceptOrReject.Reject


# updating sample function
def set_sample_fields(sample, row, field_names):
    for name in field_names & row.keys():  # updating only required fields in field_names
        field = PcmSample._meta.get_field(name)  # taking field from Sample django model
        value = row[name]  # taking value from row
        if value == '':
            value = None
        # Tabulator sends null for cleared cells; NOT NULL columns fall back to their model default
        if value is None and not field.null:
            value = field.get_default()
        try:
            setattr(sample, name, field.to_python(value))
        except ValidationError as e:
            raise ValidationError(f'{sample.lab_sample} {name}: {" ".join(e.messages)}')


class PCMSamplesDataEntryManager():
    # same two save modes as PLM data entry:
    # 'update'      - edited saved rows + new rows added at the end of the table
    # 'put' - rows were deleted or inserted above saved rows: the whole table replaces
    #                 every sample of the project, analysis results are not kept
    def __init__(self, pcm_project, input_data, mode):
        self.pcm_project = pcm_project
        self.mode = mode
        self.now_moment = timezone.now()
        if mode == 'update':
            self.data_to_update = input_data.get('updated', [])
            self.data_to_create = input_data.get('created', [])
            self.data_to_delete = input_data.get('deleted', [])
        elif mode == 'put':
            self.rows = input_data
        else:
            raise ValueError(f'unknown data entry save mode: {mode}')


    def table_update_processing(self) -> dict:
        with transaction.atomic():
            # one data entry save per project at a time: new row numbers depend on the saved samples
            PcmProject.objects.select_for_update().get(pk=self.pcm_project.pk)
            if self.mode == 'update':
                return {'status': 'ok', 'updated': self._update_data(), 'created': self._create_data(), 'deleted':self._delete_data()}
            return {'status': 'ok', **self._replace_all()}

    def _update_data(self):
        if not self.data_to_update:
            return 0
        update_ids = {int(item['id']) for item in self.data_to_update}

        samples = {sample.id : sample for sample in
                    PcmSample.objects.select_for_update().filter(pcm_project=self.pcm_project, pk__in=update_ids)}

        check_versions(samples, self.data_to_update)
        touched_fields = set()
        for element in self.data_to_update:
            sample = samples[element['id']]
            for field_name, value in element.items():
                if field_name != 'id':
                    setattr(sample, field_name, value)
                    touched_fields.add(field_name)
            setattr(sample, 'time_update', self.now_moment)
            calculate_sample_results(sample)

        # volume and results are recalculated from the edited fields
        return PcmSample.objects.bulk_update(
            samples.values(), sorted(touched_fields | {'sample_volume', 'time_update'})
        )

    def _create_data(self):
        if not self.data_to_create:
            return 0
        # in this mode new rows are only at the end of the table, after the saved samples
        last_row_number = (PcmSample.objects.filter(pcm_project=self.pcm_project)
                                            .aggregate(Max('row_number'))['row_number__max'] or 0)
        samples = [self._new_sample(row, position)
                   for position, row in enumerate(self.data_to_create, start=last_row_number + 1)]
        for sample in samples:
            calculate_sample_results(sample)
        PcmSample.objects.bulk_create(samples)
        return len(samples)

    def _delete_data(self):
        PcmSample.objects.filter(id__in=self.data_to_delete).delete()
        return len(self.data_to_delete)

    def _replace_all(self):
        # every row is built and validated before anything is deleted
        samples = [self._new_sample(row, position) for position, row in enumerate(self.rows, start=1)]
        deleted, _ = PcmSample.objects.filter(pcm_project=self.pcm_project).delete()
        PcmSample.objects.bulk_create(samples)
        return {'deleted': deleted, 'created': len(samples)}

    def _new_sample(self, row, position):
        # table order defines row numbers and lab sample ids
        sample = PcmSample(pcm_project=self.pcm_project, row_number=position,
                           lab_sample=f'{self.pcm_project.project.lab_id}-{position}')
        set_sample_fields(sample, row, PCM_ENTRY_FIELDS)
        calculate_sample_results(sample)
        return sample

class PCMSamplesAnalysisManager():
    def __init__(self, pcm_project, input_data):
        self.pcm_project = pcm_project
        self.data = input_data
        self.now_moment = timezone.now()

    def table_update_processing(self) -> dict:
        result = {'status': 'ok'}
        with transaction.atomic():
            update_ids = {int(row['id']) for row in self.data}
            samples = {sample.id : sample for sample in
                        PcmSample.objects.select_for_update().filter(pcm_project=self.pcm_project, pk__in=update_ids)}

            z_criterion = self.pcm_project.z_criterion_record
            sr = z_criterion.relative_std_deviation_low if z_criterion else None

            now = timezone.now()
            for row in self.data:
                sample = samples[int(row['id'])]
                set_sample_fields(sample, row, PCM_ANALYSIS_FIELDS)
                calculate_sample_results(sample)
                sample.qc_accept_or_reject = calculate_qc_accept_or_reject(
                    sample.fiber_per_mm, sample.qc_fiber_per_mm, sr)
                sample.time_update = self.now_moment

            result['updated'] = PcmSample.objects.bulk_update(
                samples.values(), sorted(PCM_ANALYSIS_FIELDS | PCM_RESULT_FIELDS | {'sample_volume', 'time_update'})
            )
        return result
