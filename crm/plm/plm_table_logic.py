from .models import PlmSample, PlmSampleWeight
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import django.utils

PLM_ENTRY_REQUIRED_ON_CREATE = {
    'homo_area', 'client_sample', 'lab_sample', 'description',
    'location', 'method', 'row_number', 'layer',
}

PLM_WEIGHT_REQUIRED_ON_CREATE = {'client_sample', 'w_crucible', 'w_crucible_with_sample',
                                 'w_sample', 'w_sample_ashed', 'org',
                                 'w_petri', 'w_petri_with_sample', 'residue', 'caco3' }

class PLMSamplesDataEntryManager():
    def __init__(self, plm_project, input_data, type):
        self.plm_project = plm_project
        self.input_data = input_data
        self.type = type
        if self.type == 'update':
            self.data_to_update = input_data.get('updated', [])
            self.data_to_create = input_data.get('created', [])

        self.error = None

    def validate_whole_object(self):
        if self.type == 'update':
            error = self.validate_updated_data()
            if error is not None:
                return error

            error = self.validate_created_data()
            if error is not None:
                return error

        elif self.type == 'replace_all':
            for record in self.input_data:
                missing = PLM_ENTRY_REQUIRED_ON_CREATE - set(record.keys())
                if missing:
                    return {'error': f"missing required fields"}

    def validate_updated_data(self):
        if self.data_to_update:
            for record in self.data_to_update:
                for field_name, value in record.get('fields').items():
                    if field_name == 'lab_sample':
                        if value is not None:
                            if len(str(value)) < 6:
                                return {'error': 'changed lab_id is too short'} 
                        else:
                            return {'error': 'lab_id is required'} 

    def validate_created_data(self):
        if self.data_to_create:
            for record in self.data_to_create:
                if not record.get('lab_sample'):
                    return {'error': 'lab_sample is required'} 
                
                missing = PLM_ENTRY_REQUIRED_ON_CREATE - set(record.get('fields'))
                if missing:
                    return {'error': f"missing required fields {record.get('lab_id')} : {missing}"}
                
            lab_id_list = [element.get('lab_sample') for element in self.data_to_create]
            if PlmSample.objects.filter(lab_sample__in=lab_id_list).exists():
                return {'error': 'lab_id already exist'} 

    def table_update_processing(self) -> dict:
        if self.type == 'update':
            result = {'status': 'ok'}
            with transaction.atomic():
                if self.data_to_update:
                    result['updated'] = self._update_data()
                if self.data_to_create:
                    result['created'] = self._create_data()


        elif self.type == 'replace_all':
            samples = []
            with transaction.atomic():
                PlmSample.objects.filter(plm_project=self.plm_project).delete()
                for data in self.input_data:
                    data['row_number'] = int(data['row_number'])
                    samples.append(PlmSample(plm_project=self.plm_project, **data))

                for sample in samples:
                    sample.full_clean()
                    sample.save()

            result = {'status': 'ok'}

        return result

    def _update_data(self):
        try:
            work_data = self.data_to_update
            id_list = [element.get('id') for element in work_data]
            
            touched_fields = set()

            samples_to_update = {sample.id : sample for sample in 
                                              PlmSample.objects.select_for_update().filter(pk__in=id_list)}

            for record_row in work_data:
                sample = samples_to_update[int(record_row.get('id'))]
                for name_field, value in record_row.get('fields').items():
                    setattr(sample, name_field, value)
                    touched_fields.add(name_field)

                sample.time_update = django.utils.timezone.now()

            updated = PlmSample.objects.bulk_update(
                            samples_to_update.values(), sorted(touched_fields | {'time_update'})
                        )
            
            return updated

        except Exception as e:
            return {'status':'!ok', "error": f"{str(e)}"}

    def _create_data(self):
        samples = []
        try:
            for data in self.data_to_create:
                fields = data.get('fields')
                samples.append(PlmSample(plm_project=self.plm_project, **fields))

            for sample in samples:
                sample.full_clean()
                sample.save()

            return len(samples)

        except Exception as e:
            return {'status':'!ok', "error": f"{str(e)}"}

class PLMSamplesWeightManager():
    def __init__(self, plm_project, input_data):
        self.plm_project = plm_project
        self.input_data = input_data
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])
        self.data_to_delete = input_data.get('deleted', [])

    def validate_whole_object(self):
        work_data = self.data_to_update + self.data_to_create
        print(work_data)
        for record in work_data:
            field_names = set(record.keys())
            missing = PLM_WEIGHT_REQUIRED_ON_CREATE - field_names
            if missing:
                return {'error': f"missing required fields "}

    def table_update_processing(self) -> dict:
        result = {'status': 'ok'}
        with transaction.atomic():
            if self.data_to_update:
                result['updated'] = self._update_data()
            if self.data_to_create:
                result['created'] = self._create_data()
            if self.data_to_delete:
                result['deleted'] = self._delete_data()

        return result

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

            sample.time_update = django.utils.timezone.now()

        return PlmSampleWeight.objects.bulk_update(
                        samples_to_update.values(), sorted(touched_fields | {'time_update'})
                    )

    def _create_data(self):
        weights = []
        for data in self.data_to_create:
            weights.append(PlmSampleWeight(plm_project=self.plm_project, **data))

        for weight in weights:
            weight.full_clean()
            weight.save()

        # Taking all samples for update
        samples_to_update = {sample.client_sample : sample for sample in  
                            PlmSample.objects.select_for_update().filter(plm_project=self.plm_project)}

        for data in self.data_to_create:
            weight_record = PlmSampleWeight.objects.get(client_sample=data['client_sample']) # take weight with client id
            sample_to_update = samples_to_update[data['client_sample']] #take sample with client id
            setattr(sample_to_update, 'weight', weight_record) # Filling new value 
            sample_to_update.time_update = django.utils.timezone.now()  # new time update

        # Update all samples
        PlmSample.objects.bulk_update(samples_to_update.values(), sorted({'weight', 'time_update'}))

        return len(weights)

    def _delete_data(self):
        PlmSampleWeight.objects.filter(pk__in=self.data_to_delete).delete()
        return len(self.data_to_delete)
 