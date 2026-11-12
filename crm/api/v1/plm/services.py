import django
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

        return result

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
                            PlmSampleWeight.objects.select_for_update().filter(pk__in=id_list).order_by('pk')}

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

FIELDS_TEM_FOR_UPDATE = []

FIELDS_TEM_FOR_CALCULATE = []

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

            calculate_plm_nob_analysis(samples_to_update.values())
            mark_not_analyzed_samples(list(samples_to_update.values()))
            PlmSample.objects.bulk_update(samples_to_update.values(), FIELDS_NOB_FOR_UPDATE + FIELDS_NOB_FOR_CALCULATE)

            return {'updated':len(payload_json)}

        for record_row in payload_json:
            sample = samples_to_update[record_row.get('id')]
            for field in FIELDS_TEM_FOR_UPDATE:
                if record_row[field] is None and not PlmSample._meta.get_field(field).null:
                    record_row[field] = PlmSample._meta.get_field(field).get_default()
                setattr(sample, field, record_row[field])

            if 'tem_grid_box' in record_row and 'tem_grid_box_id_1' in record_row and 'tem_grid_box_id_2' in record_row:
                TEMGridRecord.objects.filter(grid_box=record_row['tem_grid_box'],
                                             grid_id_1=record_row['tem_grid_box_id_1'],
                                             grid_id_2=record_row['tem_grid_box_id_2'],
                                             qc=False).update(
                    plm_tem_project=selected_plm_project,
                    plm_tem_sample=sample,
                    filled=True,
                )

            sample.version += 1

        calculate_plm_nob_analysis(samples_to_update.values())
        mark_not_analyzed_samples(list(samples_to_update.values()))
        PlmSample.objects.bulk_update(samples_to_update.values(), FIELDS_NOB_FOR_UPDATE + FIELDS_NOB_FOR_CALCULATE)

        return {'updated': len(payload_json)}


ASB_OIL_PARAMETERS = {2: {'delta':{19:'1.557', 20:'1.557',
                                        21:'1.556', 22:'1.556',
                                        23: '1.555', 24: '1.555',
                                        25: '1.554', 26: '1.554',
                                        27: '1.553'},
                                'alpha': {19:'1.552', 20:'1.552',
                                        21:'1.551', 22:'1.551',
                                        23: '1.550', 24: '1.550',
                                        25: '1.549', 26: '1.549',
                                        27: '1.548'}},
                5: {'delta':{19:'1.626', 20:'1.626',
                                        21:'1.625', 22:'1.625',
                                        23: '1.625', 24: '1.625',
                                        25: '1.624', 26: '1.624',
                                        27: '1.623'},
                                'alpha': {19:'1.611', 20:'1.611',
                                        21:'1.611', 22:'1.611',
                                        23: '1.610', 24: '1.610',
                                        25: '1.609', 26: '1.609',
                                        27: '1.608'}},
                3: {'delta': {19:'1.700', 20:'1.700',
                                        21:'1.699',  22:'1.699',
                                        23: '1.698', 24: '1.698',
                                        25: '1.698', 26: '1.698',
                                        27: '1.697'},
                                'alpha': {19:'1.682', 20:'1.682',
                                        21:'1.681', 22:'1.681',
                                        23: '1.680', 24: '1.680',
                                        25: '1.679', 26: '1.679',
                                        27: '1.678'}}}

ASBESTOS_PARAMETERS = {
    2: {'morphology': 1, 'sign_of_elongation': 1, 'extinction_angle': 1, 'pleochroism_color': 1, 'birefringence': 1},
    3: {'morphology': 2, 'sign_of_elongation': 1, 'extinction_angle': 1, 'pleochroism_color': 1, 'birefringence': 2},
    4: {'morphology': 2, 'sign_of_elongation': 2, 'extinction_angle': 1, 'pleochroism_color': 2, 'birefringence': 2},
    5: {'morphology': 2, 'sign_of_elongation': 1, 'extinction_angle': 1, 'pleochroism_color': 1, 'birefringence': 2},
    6: {'morphology': 2, 'sign_of_elongation': 1, 'extinction_angle': 2, 'pleochroism_color': 1, 'birefringence': 2},
    7: {'morphology': 2, 'sign_of_elongation': 1, 'extinction_angle': 2, 'pleochroism_color': 1, 'birefringence': 2},
};

ASB_TYPES_ARRAY = [SampleASbestosType.Chry,
                   SampleASbestosType.Amo,
                   SampleASbestosType.Croc,
                   SampleASbestosType.Anth,
                    SampleASbestosType.Trem,
                    SampleASbestosType.Act]

def _round(value, places='0.01'):
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)

def calculate_asbestos_percent(sample):
    if sample.asb_point_1 == 50 and sample.asb_point_2 == 50 and sample.asb_point_3 == 50 and sample.asb_point_4 == 50:
        count_points = 0
        for point in [sample.asb_point_5 + sample.asb_point_6 + sample.asb_point_7 + sample.asb_point_8]:
            if point != 50:
                count_points += 1
        sample.asb_percent = _round(count_points / 4)
    else:
        sum_point = sum([sample.asb_point_1, sample.asb_point_2, sample.asb_point_3, sample.asb_point_4])
        if sample.method == SampleMethod.Sample1981:
            sample.asb_percent = _round((400 / Decimal(sum_point)))
        else:
            sample.asb_percent = _round((400 / Decimal(sum_point) * sample.weight.residue) / 100)



def calculate_plm_nob_analysis(samples):
    for sample in samples:
        sample.other_fiber = sample.other_fiber_property
        if sample.asb_type in ASB_TYPES_ARRAY:
            sample.ri_alpha_oil = ASB_OIL_PARAMETERS[sample.asb_type]['alpha'][sample.analysis_temperature]
            sample.ri_delta_oil = ASB_OIL_PARAMETERS[sample.asb_type]['delta'][sample.analysis_temperature]
            sample.morphology = ASBESTOS_PARAMETERS[sample.asb_type]['morphology']
            sample.sign_of_elongation = ASBESTOS_PARAMETERS[sample.asb_type]['sign_of_elongation']
            sample.extinction_angle = ASBESTOS_PARAMETERS[sample.asb_type]['extinction_angle']
            sample.pleochroism_color = ASBESTOS_PARAMETERS[sample.asb_type]['pleochroism_color']
            sample.birefringence = ASBESTOS_PARAMETERS[sample.asb_type]['birefringence']

            calculate_asbestos_percent(sample)
        elif (sample.asb_type in [SampleASbestosType.NAD, SampleASbestosType.NotSubmitted]) or sample.asb_type is None:
            sample.ri_alpha_oil = None
            sample.ri_delta_oil = None
            sample.morphology = None
            sample.sign_of_elongation = None
            sample.extinction_angle = None
            sample.pleochroism_color = None
            sample.birefringence = None
            sample.asb_point_1 = 50
            sample.asb_point_2 = 50
            sample.asb_point_3 = 50
            sample.asb_point_4 = 50
            sample.asb_point_5 = 50
            sample.asb_point_6 = 50
            sample.asb_point_7 = 50
            sample.asb_point_8 = 50
            sample.tem_na_or_ps = None


def mark_not_analyzed_samples(samples):
    for sample in samples:
        if (sample.asb_type in ASB_TYPES_ARRAY and sample.asb_percent > 1):
            if (sample.method != SampleMethod.Sample1981):
                sample.tem_na_or_ps = 'PS'
            index = samples.index(sample)
            for another_sample in samples[index + 1:]:
                if another_sample.is_original_sample():
                    if ( another_sample.homo_area == sample.homo_area
                      and another_sample.asb_type != SampleASbestosType.NotSubmitted):
                        another_sample.asb_type = SampleASbestosType.NotAnalyzed
                        if (another_sample.method != SampleMethod.Sample1981):
                            another_sample.tem_na_or_ps = 'PS'
        else:
            index = samples.index(sample)
            if (sample.method != SampleMethod.Sample1981):
                sample.tem_na_or_ps = 'PS'
            for another_sample in samples[index + 1:]:
                if another_sample.is_original_sample():
                    if ( another_sample.homo_area == sample.homo_area
                      and another_sample.asb_type == SampleASbestosType.NotAnalyzed):
                        another_sample.asb_type = SampleASbestosType.NAD
                        if (another_sample.method != SampleMethod.Sample1981):
                            another_sample.tem_na_or_ps = None
