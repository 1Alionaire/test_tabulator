import django
from django.db.models import F
from django.utils import timezone
from django.db import transaction

from plm.models import PlmSample, PlmSampleWeight, SampleMethod, SampleASbestosType
from tem.models import TEMGridRecord
from api.v1.utils import check_versions

from decimal import Decimal, ROUND_HALF_UP

class PLMSamplesEntryManager():
    def __init__(self, plm_project, input_data, mode):
        self.plm_project = plm_project
        self.input_data = input_data
        self.mode = mode
        if self.mode == 'patch':
            self.data_to_update = input_data.get('updated', [])
            self.data_to_create = input_data.get('created', [])
            self.data_to_delete = input_data.get('deleted', [])

    def table_update_processing(self) -> dict:
        if self.mode == 'patch':
            result = {}
            with transaction.atomic():
                if self.data_to_delete:
                    result['deleted'] = self._delete_data()
                if self.data_to_update:
                    result['updated'] = self._update_data()
                if self.data_to_create:
                    result['created'] = self._create_data()

        elif self.mode == 'put':
            samples = []
            with transaction.atomic():
                PlmSample.objects.filter(plm_project=self.plm_project).delete()
                for data in self.input_data:
                    samples.append(PlmSample(plm_project=self.plm_project, **data))

                for sample in samples:
                    sample.save()

            result = {'created':len(samples)}

        (PlmSample.objects
         .filter(plm_project=self.plm_project, tem_asb_type_grid_1=None, tem_asb_type_grid_2=None).
         exclude(method=SampleMethod.Sample1981).
         update(tem_asb_type_grid_1=SampleASbestosType.NAD,
                tem_asb_type_grid_2=SampleASbestosType.NAD,
                tem_microscope_alignment='Y',
                tem_eccentricity_adjusted='Y',
                tem_grid_pre_acceptability='Y',
                version=F('version') + 1))

        return result

    def filling_tem_asb_result(self):
        pass


    def _update_data(self):
        work_data = self.data_to_update
        update_ids = {int(item['id']) for item in work_data}
        touched_fields = set()

        samples_to_update = {sample.id: sample for sample in
                             PlmSample.objects.select_for_update().filter(pk__in=update_ids).order_by('id')}

        check_versions(samples_to_update, work_data)

        for element in work_data:
            sample = samples_to_update[int(element['id'])]
            for field_name, value in element.items():
                if field_name != 'id':
                    setattr(sample, field_name, value)
                    touched_fields.add(field_name)
            sample.version += 1

        return PlmSample.objects.bulk_update(
            samples_to_update.values(), sorted(touched_fields | { 'version'})
        )

    def _create_data(self):
        samples = []
        for data in self.data_to_create:
            samples.append(PlmSample(plm_project=self.plm_project, **data))

        for sample in samples:
            sample.save()

        return len(samples)

    def _delete_data(self):
        PlmSample.objects.filter(id__in=self.data_to_delete).delete()
        return len(self.data_to_delete)

class PLMSamplesWeightManager():
    def __init__(self, plm_project, input_data):
        self.plm_project = plm_project
        self.input_data = input_data
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])
        self.data_to_delete = input_data.get('deleted', [])
        self.now_moment = django.utils.timezone.now()

    def table_update_processing(self) -> dict:
        result = {}
        with transaction.atomic():
            if self.data_to_update:
                result['updated'] = self._update_data()
            if self.data_to_create:
                result['created'] = self._create_data()
            if self.data_to_delete:
                result['deleted'] = self._delete_data()

            self._update_plm_samples()

        return result

    def _update_plm_samples(self):
        PlmSample.objects.filter(plm_project=self.plm_project).exclude(method=SampleMethod.Sample1981).update(
            weight=None)

        samples_to_update = {sample.client_sample: sample for sample in
                             PlmSample.objects.select_for_update().filter(plm_project=self.plm_project).exclude(
                                 method=SampleMethod.Sample1981).order_by('pk')}

        for client_id, sample_object in samples_to_update.items():
            weight_record = PlmSampleWeight.objects.filter(plm_project=self.plm_project,
                                                           client_sample=client_id).first()
            if weight_record:
                setattr(sample_object, 'weight', weight_record)  # Filling new value
                sample_object.version += 1

        # Update all samples
        PlmSample.objects.bulk_update(samples_to_update.values(), sorted({'weight', 'version'}))

    def _update_data(self):
        work_data = self.data_to_update
        id_list = [element.get('id') for element in work_data]
        touched_fields = set()

        samples_to_update = {sample.id : sample for sample in
                            PlmSampleWeight.objects.
                            select_for_update().
                            filter(pk__in=id_list).order_by('pk')}

        check_versions(samples_to_update, work_data)

        for record_row in work_data:
            sample = samples_to_update[int(record_row.get('id'))]
            for name_field, value in record_row.items():
                if name_field != 'id':
                    setattr(sample, name_field, value)
                    touched_fields.add(name_field)
                if value is None and not PlmSampleWeight._meta.get_field(name_field).null:
                    value = PlmSampleWeight._meta.get_field(name_field).get_default()
            sample.version += 1

        updated = PlmSampleWeight.objects.bulk_update(
                        samples_to_update.values(), sorted(touched_fields | {'version'})
                    )

        return updated

    def _create_data(self):
        return PlmSampleWeight.objects.bulk_create([PlmSampleWeight(plm_project=self.plm_project,
                                                                    **data) for data in self.data_to_create])

    def _delete_data(self):
        PlmSampleWeight.objects.filter(pk__in=self.data_to_delete).delete()
        return len(self.data_to_delete)

FIELDS_NOB_FOR_UPDATE = ['color', 'other_fiber', 'other_fiber_percent', 'asb_type', 'analysis_temperature',
                        'asb_point_1', 'asb_point_2', 'asb_point_3', 'asb_point_4',
                        'asb_point_5', 'asb_point_6', 'asb_point_7', 'asb_point_8', 'texture', 'version']

FIELDS_NOB_FOR_CALCULATE = ['other_fiber_property', 'ri_alpha_oil', 'ri_delta_oil', 'morphology',
                            'sign_of_elongation', 'extinction_angle', 'pleochroism_color', 'birefringence',
                            'tem_na_or_ps', 'asb_percent']

FIELDS_TEM_FOR_UPDATE = ['tem_asb_type_grid_1', 'tem_asb_point_grid_1', 'tem_asb_type_grid_2', 'tem_asb_point_grid_2',
                   'tem_grid_box', 'tem_grid_box_id_1', 'tem_grid_box_id_2', 'version']

FIELDS_TEM_FOR_CALCULATE = ['tem_asb_percent_grid_1', 'tem_asb_percent_grid_2', 'tem_asb_type_total', 'tem_asb_percent_total', 'tem_na_or_ps']

def update_plm_nob_tem_analysis(payload_json, selected_plm_project, type='nob'):
    with transaction.atomic():
        samples_to_update = {sample.id: sample for sample in
                             PlmSample.objects.select_related('weight').select_for_update().filter(plm_project=selected_plm_project).order_by('row_number')}

        check_versions(samples_to_update, payload_json)
        if type == 'nob':
            for record_row in payload_json:
                sample = samples_to_update[record_row.get('id')]
                for field in FIELDS_NOB_FOR_UPDATE:
                    if record_row[field] is None and not PlmSample._meta.get_field(field).null:
                        record_row[field] = PlmSample._meta.get_field(field).get_default()
                    setattr(sample, field, record_row[field])

                sample.version += 1

            calculate_plm_nob_analysis(list(samples_to_update.values()))
            PlmSample.objects.bulk_update(samples_to_update.values(), FIELDS_NOB_FOR_UPDATE + FIELDS_NOB_FOR_CALCULATE)

            return {'updated':len(payload_json)}

        for record_row in payload_json:
            sample = samples_to_update[record_row.get('id')]
            for field in FIELDS_TEM_FOR_UPDATE:
                if record_row[field] is None and not PlmSample._meta.get_field(field).null:
                    record_row[field] = PlmSample._meta.get_field(field).get_default()
                setattr(sample, field, record_row[field])

                sample.calculate_tem_result()
                sample.write_tem_asb_result()

            TEMGridRecord.objects.filter(grid_box=record_row['tem_grid_box'],
                                         grid_id_1=record_row['tem_grid_box_id_1'],
                                         grid_id_2=record_row['tem_grid_box_id_2'],
                                         qc=False).update(
                plm_tem_project=selected_plm_project,
                plm_tem_sample=sample,
                filled=True,
            )

            sample.version += 1

        mark_tem_not_analyzed_samples(list(samples_to_update.values()))

        PlmSample.objects.bulk_update(samples_to_update.values(), FIELDS_TEM_FOR_CALCULATE + FIELDS_TEM_FOR_UPDATE)

        return {'updated': len(payload_json)}

ASB_TYPES_ARRAY = [SampleASbestosType.Chry,
                   SampleASbestosType.Amo,
                   SampleASbestosType.Croc,
                   SampleASbestosType.Anth,
                    SampleASbestosType.Trem,
                    SampleASbestosType.Act]

def _round(value, places='0.01'):
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)

def calculate_plm_nob_analysis(samples):
    for sample in samples: # start loop
        sample.other_fiber = sample.other_fiber_property # make secondary column
        if sample.asb_type in ASB_TYPES_ARRAY: # if sample asb positive
            sample.plm_nob_parameter_fill() # filling all asb parameters
            sample.calculate_plm_nob_asb_percent() #calculate asb_percent
            # if asb_percent > 1%, all original sample with same homo area(but going after sample) must be marked as 'Not analyzed'
            if sample.asb_percent > 1:
                sample.tem_na_or_ps = 'PS' # mark that is not analyzed in TEM
                start_index = samples.index(sample) + 1 # take index for slicing
                for another_sample in samples[start_index:]: # going through another samples
                    if another_sample.is_original_sample(): # if sample is not QC
                        # same Homo area and submitted sample
                        if (another_sample.homo_area == sample.homo_area
                                and another_sample.asb_type != SampleASbestosType.NotSubmitted):
                            another_sample.asb_type = SampleASbestosType.NotAnalyzed # mark "Not analyzed"
                            another_sample.tem_na_or_ps = 'PS' # mark that is not analyzed in TEM

        # If we change asb result from asb positive to asb negative
        elif sample.asb_type == SampleASbestosType.NAD:
            sample.plm_nob_parameter_clean() # clean all asb parameters
            sample.tem_na_or_ps = None  # analyzable for TEM
            start_index = samples.index(sample) + 1 # take index for slicing
            for another_sample in samples[start_index:]:
                if another_sample.is_original_sample(): # going through another samples
                    # same Homo area and "NotAnalyzed" before
                    if (another_sample.homo_area == sample.homo_area
                            and another_sample.asb_type == SampleASbestosType.NotAnalyzed):
                        another_sample.asb_type = SampleASbestosType.NAD # mark NAD
                        another_sample.tem_na_or_ps = None # mark that is analyzable for TEM

def mark_tem_not_analyzed_samples(samples):
    for sample in samples:
        if sample.is_sample_tem_has_asbest() and sample.tem_asb_percent_total > 1:
            start_index = samples.index(sample) + 1
            for another_sample in samples[start_index:]:
                if another_sample.is_original_sample():
                    if another_sample.homo_area == sample.homo_area:
                        another_sample.tem_asb_type_grid_1 = SampleASbestosType.NotAnalyzed
                        another_sample.tem_asb_type_grid_2 = SampleASbestosType.NotAnalyzed
                        another_sample.tem_na_or_ps = 'PS'


        elif sample.is_sample_tem_clean() and sample.asb_percent < 1:
            sample.tem_asb_percent_grid_1 = 0
            sample.tem_asb_percent_grid_2 = 0
            sample.tem_asb_point_grid_1 = 0
            sample.tem_asb_point_grid_2 = 0
            start_index = samples.index(sample) + 1
            for another_sample in samples[start_index:]:
                if another_sample.is_original_sample():
                    if another_sample.homo_area == sample.homo_area:
                        another_sample.tem_asb_type_grid_1 = SampleASbestosType.NAD
                        another_sample.tem_asb_type_grid_2 = SampleASbestosType.NAD
                        another_sample.tem_na_or_ps = None

        elif sample.is_sample_tem_not_analyzed() or sample.asb_type == SampleASbestosType.NotAnalyzed:
            sample.tem_na_or_ps = 'PS'

        sample.write_tem_asb_result()