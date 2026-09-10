from .models import PlmSample 
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import django.utils

REQUIRED_ON_CREATE = {
    'homo_area', 'client_sample', 'lab_sample', 'description',
    'location', 'method', 'row_number'
}

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
                missing = REQUIRED_ON_CREATE - set(record.keys())
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
                
                missing = REQUIRED_ON_CREATE - set(record.get('fields'))
                if missing:
                    return {'error': f"missing required fields {record.get('lab_id')} : {missing}"}
                
            lab_id_list = [element.get('lab_sample') for element in self.data_to_create]
            if PlmSample.objects.filter(lab_sample__in=lab_id_list).exists():
                return {'error': 'lab_id already exist'} 

    def table_update_processing(self) -> dict:
        if self.type == 'update':
            try:
                with transaction.atomic():
                    updated = self.update_data() if self.data_to_update else 0
                    created = self.create_data() if self.data_to_create else 0
            except Exception as e:
                return {'status': '!ok', 'error': e.message_dict if hasattr(e, 'message_dict') else e.messages}

            result = {'status': 'ok'}
            if updated != 0 :
                result['updated'] = updated
            if created != 0:
                result['created'] = created

        elif self.type == 'replace_all':
            samples = []
            try:
                with transaction.atomic():
                    PlmSample.objects.filter(plm_project=self.plm_project).delete()
                    for data in self.input_data:
                        data['row_number'] = int(data['row_number'])
                        samples.append(PlmSample(plm_project=self.plm_project, **data))

                    for sample in samples:
                        sample.full_clean()
                        sample.save()

                result = {'status': 'ok'}

            except Exception as e:
                return {'status': '!ok', 'error': e.message_dict if hasattr(e, 'message_dict') else e.messages}

        return result

    def update_data(self):
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

    def create_data(self):
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

