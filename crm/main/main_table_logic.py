from django.shortcuts import render
from .models import MainProject, TypeAnalysis, TurnAroundTime, ProjectStatus
from django.http import JsonResponse, FileResponse
from finance.models import Company
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.db import transaction
import django.utils
from dataclasses import dataclass

REQUIRED_ON_CREATE = {
    'company_id', 'project_name', 'project_address', 'date_registered', 'time_registered',
    'sample_type_id', 'number_samples', 'turn_around_time_id'
}

class MainProjectTableManager():
    def __init__(self, input_data):
        self.input_data = input_data
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])

        self.error = None

    def validate_whole_object(self):
        error = self.validate_updated_data()
        if error is not None:
            return error

        error = self.validate_created_data()
        if error is not None:
            return error

    def validate_updated_data(self):
        if self.data_to_update:
            for record in self.data_to_update:
                for field_name, value in record.get('fields').items():
                    if field_name == 'lab_id':
                        if value is not None:
                            if len(str(value)) < 6:
                                return {'error': 'changed lab_id is too short'} 
                        else:
                            return {'error': 'lab_id is required'} 

    def validate_created_data(self):
        if self.data_to_create:
            for record in self.data_to_create:
                if not record.get('lab_id'):
                    return {'error': 'lab_id is required'} 
                
                missing = REQUIRED_ON_CREATE - set(record.get('fields'))
                if missing:
                    return {'error': f"missing required fields {record.get('lab_id')} : {missing}"}
                
            lab_id_list = [element.get('lab_id') for element in self.data_to_create]
            if MainProject.objects.filter(lab_id__in=lab_id_list).exists():
                return {'error': 'lab_id already exist'} 

    def table_update_processing(self) -> dict:
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

        return result
            
    def update_data(self):
        try:
            work_data = self.data_to_update
            id_list = [element.get('id') for element in work_data]
            touched_fields = set()

            projects_to_update = {project.id : project for project in 
                                  MainProject.objects.select_for_update().filter(pk__in=id_list)}

            for record_row in work_data:
                project = projects_to_update[int(record_row.get('id'))]
                for name_field, value in record_row.get('fields').items():
                    setattr(project, name_field, value)
                    touched_fields.add(name_field)
                project.time_update = django.utils.timezone.now()

            updated = MainProject.objects.bulk_update(
                projects_to_update.values(), sorted(touched_fields | {'time_update'})
            )
            
            return updated

        except Exception as e:
            return {'status':'!ok', "error": f"{str(e)}"} 


    def create_data(self):
        objects = []
        try:
            for data in self.data_to_create:
                fields = data.get('fields')
                objects.append(MainProject(status_id=1, **fields))

            for project in objects:
                project.full_clean()
                project.save()

            return len(objects)

        except Exception as e:
            return {'status':'!ok', "error": f"{str(e)}"} 
        
        
    def delete_data(self):
        pass
