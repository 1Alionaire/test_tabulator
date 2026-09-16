from .models import MainProject
from django.db import transaction
from plm.models import PlmProject, PlmSample, PlmSampleWeight
import django.utils
from utils.utils import generate_rand_string_4

REQUIRED_ON_CREATE = {
    'company_id', 'project_name', 'project_address', 'date_registered', 'time_registered',
    'sample_type_id', 'number_samples', 'turn_around_time_id'
}

class MainProjectTableManager():
    def __init__(self, input_data):
        self.input_data = input_data
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])
        self.data_to_delete = input_data.get('deleted', [])

        self.error = None

    def validate_whole_object(self):
        error = self.validate_updated_data()
        if error is not None:
            return error

        error = self.validate_created_data()
        if error is not None:
            return error

        error = self.validate_deleted_data()
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
            if MainProject.active_objects.filter(lab_id__in=lab_id_list).exists():
                return {'error': 'lab_id already exist'} 

    def validate_deleted_data(self):
        if self.data_to_delete:
            if MainProject.active_objects.filter(id__in=self.data_to_delete).exists() == False:
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

        projects_to_update = {project.id : project for project in 
                                MainProject.active_objects.select_for_update().filter(pk__in=id_list)}

        for record_row in work_data:
            project = projects_to_update[int(record_row.get('id'))]
            for name_field, value in record_row.get('fields').items():
                setattr(project, name_field, value)
                touched_fields.add(name_field)
                if name_field == 'lab_id':
                    new_lab_id_sort = MainProject._make_sort_key(value)
                    setattr(project, 'lab_id_sort', new_lab_id_sort)
                    touched_fields.add('lab_id_sort')

            project.time_update = django.utils.timezone.now()

        return MainProject.active_objects.bulk_update(
            projects_to_update.values(), sorted(touched_fields | {'time_update'})
        )

    def _create_data(self):
        objects = []
        for data in self.data_to_create:
            fields = data.get('fields')
            objects.append(MainProject(status_id=1, deleted=False,  **fields))

        for project in objects:
            project.full_clean()
            project.save()
            creating_signal_manager = ProjectCreateSignal(project)
            creating_signal_manager.create_project()

        return len(objects)
        
    def _delete_data(self): 
        projects_to_update = {project.id : project for project in 
                                            MainProject.active_objects.select_for_update().filter(pk__in=self.data_to_delete)}
        for project in projects_to_update.values():
            previous_lab_id = project.lab_id
            new_lab_id = previous_lab_id + '-del-' + generate_rand_string_4()
            setattr(project, 'lab_id', new_lab_id)
            setattr(project, 'lab_id_sort', MainProject._make_sort_key(new_lab_id))
            setattr(project, 'deleted', True)
            setattr(project, 'time_update', django.utils.timezone.now())

        return MainProject.active_objects.bulk_update(
            projects_to_update.values(), sorted({'lab_id', 'lab_id_sort', 'deleted', 'time_update'})
        )


class ProjectCreateSignal:
    def __init__(self, main_project):
        self.main_project = main_project

    def create_project(self):
        print(self.main_project.sample_type)
        if self.main_project.sample_type_id in [2, 3, 4]:
            self.create_plm_project()

    def create_plm_project(self):
        created_plm_project=PlmProject.objects.create(project=self.main_project)
        created_plm_project.save()
        amount_plm_samples = self.main_project.number_samples
        amount_nob_samples = self.main_project.nob_number_samples
        sum_samples = amount_plm_samples + amount_nob_samples
        for i in range(sum_samples):
            sample = PlmSample.objects.create(plm_project = created_plm_project,
                                            row_number=(i+1),
                                            lab_sample=str(self.main_project.lab_id) + '-' + str(i+1), 
                                            method = 1, 
                                            )
            sample.save()
        if amount_nob_samples > 0:
            for i in range(amount_nob_samples):
                weight_item = PlmSampleWeight.objects.create(plm_project = created_plm_project)
                weight_item.save()