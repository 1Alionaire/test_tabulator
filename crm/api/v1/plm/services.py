import django
from django.utils import timezone
from django.db import transaction

from plm.models import PlmProject, PlmSample, PlmSampleWeight, SampleMethod
from tem.models import TEMGridRecord


class PLMSamplesEntryManager():
    def __init__(self, plm_project, input_data, mode):
        self.plm_project = plm_project
        self.input_data = input_data
        self.now_moment = timezone.now()
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
                             PlmSample.objects.select_for_update().filter(pk__in=update_ids)}

        for element in work_data:
            print(f'element : {element}')
            sample = samples_to_update[int(element['id'])]
            for field_name, value in element.items():
                if field_name != 'id':
                    setattr(sample, field_name, value)
                    touched_fields.add(field_name)
            setattr(sample, 'time_update', self.now_moment)

        return PlmSample.objects.bulk_update(
            samples_to_update.values(), sorted(touched_fields | {'time_update'})
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
                                 method=SampleMethod.Sample1981)}

        for client_id, sample_object in samples_to_update.items():
            weight_record = PlmSampleWeight.objects.filter(plm_project=self.plm_project,
                                                           client_sample=client_id).first()
            if weight_record:
                setattr(sample_object, 'weight', weight_record)  # Filling new value
                setattr(sample_object, 'time_update', django.utils.timezone.now())  # new time update

        # Update all samples
        PlmSample.objects.bulk_update(samples_to_update.values(), sorted({'weight', 'time_update'}))

    def _update_data(self):
        work_data = self.data_to_update
        id_list = [element.get('id') for element in work_data]
        touched_fields = set()

        samples_to_update = {sample.id : sample for sample in
                            PlmSampleWeight.objects.select_for_update().filter(pk__in=id_list)}

        for record_row in work_data:
            sample = samples_to_update[int(record_row.get('id'))]
            for name_field, value in record_row.items():
                if name_field != 'id':
                    setattr(sample, name_field, value)
                    touched_fields.add(name_field)
            setattr(sample, 'time_update', self.now_moment)

        updated = PlmSampleWeight.objects.bulk_update(
                        samples_to_update.values(), sorted(touched_fields | {'time_update'})
                    )

        return updated

    def _create_data(self):
        weights = []
        for data in self.data_to_create:
            weights.append(PlmSampleWeight(plm_project=self.plm_project, **data))

        for weight in weights:
            weight.save()

        # Taking all samples for update
        samples_to_update = {sample.client_sample : sample for sample in
                            PlmSample.objects.select_for_update().filter(plm_project=self.plm_project)}

        for data in self.data_to_create:
            weight_record = PlmSampleWeight.objects.get(client_sample=data['client_sample']) # take weight with client id
            sample_to_update = samples_to_update[data['client_sample']] #take sample with client id
            setattr(sample_to_update, 'weight', weight_record) # Filling new value
            setattr(sample_to_update, 'time_update', self.now_moment)

        # Update all samples
        PlmSample.objects.bulk_update(samples_to_update.values(), sorted({'weight', 'time_update'}))

        return len(weights)

    def _delete_data(self):
        PlmSampleWeight.objects.filter(pk__in=self.data_to_delete).delete()
        return len(self.data_to_delete)

def update_plm_nob_tem_analysis(payload_json, selected_plm_project):
    with transaction.atomic():
        touched_fields = set()
        samples_to_update = {sample.id: sample for sample in
                             PlmSample.objects.select_for_update().filter(plm_project=selected_plm_project)}

        for record_row in payload_json:
            sample = samples_to_update[int(record_row.get('id'))]
            for name_field, value in record_row.items():
                if name_field not in ['id', 'weight__residue']:
                    # Tabulator sends null for cleared cells; NOT NULL columns fall back to their model default
                    if value is None and not PlmSample._meta.get_field(name_field).null:
                        value = PlmSample._meta.get_field(name_field).get_default()
                    setattr(sample, name_field, value)
                    touched_fields.add(name_field)

            if 'tem_grid_box' in record_row and 'tem_grid_box_id_1' in record_row and 'tem_grid_box_id_2' in record_row:
                TEMGridRecord.objects.filter(grid_box=record_row['tem_grid_box'],
                                             grid_id_1=record_row['tem_grid_box_id_1'],
                                             grid_id_2=record_row['tem_grid_box_id_2'],
                                             qc=False).update(
                    plm_tem_project=selected_plm_project,
                    plm_tem_sample=sample,
                    filled=True,
                )

            setattr(sample, 'time_update', django.utils.timezone.now())

        PlmSample.objects.bulk_update(samples_to_update.values(), sorted(touched_fields | {'time_update'}))

        return {'updated':len(payload_json)}
