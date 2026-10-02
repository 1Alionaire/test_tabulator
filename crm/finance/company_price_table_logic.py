from .models import Company
from django.db import transaction
from django.db.models import Q
import django.utils
from utils.utils import generate_rand_string_4
import math

class CompanyPriceTableManager():
    def __init__(self, input_data):
        self.input_data = input_data
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])
        self.data_to_delete = input_data.get('deleted', [])

        self.error = None

    def validate_whole_object(self):
        error = self.validate_created_data()
        if error is not None:
            return error

        error = self.validate_deleted_data()
        if error is not None:
            return error

    def validate_created_data(self):
        if self.data_to_create:
            for record in self.data_to_create:
                if not record.get('name'):
                    return {'error': 'name is required'} 
                
            name_list = [element.get('name') for element in self.data_to_create]
            if Company.objects.filter(name__in=name_list).exists():
                return {'error': 'name already exist'} 

    def validate_deleted_data(self):
        if self.data_to_delete:
            if Company.active_objects.filter(id__in=self.data_to_delete).exists() == False:
                return {'error': 'records dont exist'}

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

        companies_to_update = {project.id : project for project in 
                                Company.objects.select_for_update().filter(pk__in=id_list)}

        for record_row in work_data:
            company = companies_to_update[int(record_row.get('id'))]
            for name_field, value in record_row.get('fields').items():
                setattr(company, name_field, value)
                touched_fields.add(name_field)

            company.time_update = django.utils.timezone.now()

        return Company.objects.bulk_update(
            companies_to_update.values(), sorted(touched_fields | {'time_update'})
        )

    def _create_data(self):
        objects = []
        for data in self.data_to_create:
            fields = data.get('fields')
            objects.append(Company(**fields))

        for project in objects:
            project.full_clean()
            project.save()

        return len(objects)

