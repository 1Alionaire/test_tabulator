from .models import MainProject, MainTypeAnalysis, MainProjectStatus, MainTurnAroundTime
from django.db import transaction
from plm.models import PlmProject, PlmSample, PlmSampleWeight
from pcm.models import PcmProject, PcmSample
from tem.models import TEMGridRecord
from django.db.models import Q
import django.utils
from utils.utils import generate_rand_string_4
import math
from django.shortcuts import get_object_or_404

REQUIRED_ON_CREATE = {
    'company_id', 'project_name', 'project_address', 'date_registered', 'time_registered',
    'project_type', 'number_samples', 'turn_around_time'
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
        if not self.data_to_update:
            return None

        ids = {
            int(record['id'])
            for record in self.data_to_update
        }

        found = set(
            MainProject.active_objects
            .filter(id__in=ids)
            .values_list('id', flat=True)
        )

        missing = ids - found

        if missing:
            return {
                'error': f'records dont exist: {sorted(missing)}'
            }
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
            ids = {int(i) for i in self.data_to_delete}
            found = set(MainProject.active_objects.filter(id__in=ids).values_list('id', flat=True))
            missing = ids - found
            if missing:
                return {'error': f'records dont exist: {sorted(missing)}'}


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
            objects.append(MainProject(status=MainProjectStatus.New, deleted=False,  **fields))

        for project in objects:
            project.full_clean()
            project.save()
            MainProjectCreateSignal(project).create_project()

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

        # release TEM grid slots held by deleted projects (bulk_update doesn't fire save signals)
        deleted_ids = list(projects_to_update)
        PlmSample.objects.filter(plm_project__project_id__in=deleted_ids).update(
            tem_grid_box=None,
            tem_grid_box_id_1=None,
            tem_grid_box_id_2=None,
        )
        TEMGridRecord.objects.filter(
            Q(plm_tem_project__project_id__in=deleted_ids)
            | Q(plm_tem_sample__plm_project__project_id__in=deleted_ids)
        ).update(plm_tem_project=None, plm_tem_sample=None, filled=False)

        return MainProject.active_objects.bulk_update(
            projects_to_update.values(), sorted({'lab_id', 'lab_id_sort', 'deleted', 'time_update'})
        )


class MainProjectCreateSignal:
    def __init__(self, main_project):
        self.main_project = main_project

    def create_project(self):
        if self.main_project.project_type == MainTypeAnalysis.PCM:
            self.create_pcm_project()
        if self.main_project.project_type in [MainTypeAnalysis.Bulk, MainTypeAnalysis.BulkTEM, MainTypeAnalysis.TEM]:
            self.create_plm_project()

    def create_pcm_project(self):
        created_pcm_project = PcmProject.objects.create(project=self.main_project) # Create PCM project entity
        # bulk create PCM samples
        PcmSample.objects.bulk_create([ 
            PcmSample(pcm_project=created_pcm_project,
                      row_number=(i+1),
                      lab_sample=str(self.main_project.lab_id) + '-' + str(i+1))
            for i in range(self.main_project.number_samples)
        ])

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
            amount_blanks = math.ceil(amount_nob_samples/100)
            for i in range(amount_blanks):
                sample = PlmSample.objects.create(plm_project = created_plm_project,
                                                                row_number=(i+1000),
                                                                method = 3,
                                                                is_blank = True,
                                                                description = "Blank",
                                                                location = "Blank", 
                                                                client_sample = "BL" + str(i+1),
                                                                lab_sample = "BL" + str(i+1))
                
                weight_item = PlmSampleWeight.objects.create(plm_project = created_plm_project,
                                                             client_sample =  "BL" + str(i+1))
                setattr(sample, 'weight', weight_item)
                sample.save()
                weight_item.save()

class MainProjectUpdateSignal:
    def __init__(self, input_project):
        if isinstance(input_project, PcmProject):
            self.main_project_query = MainProject.objects.filter(pcm_project = input_project)
        if isinstance(input_project, PlmProject):
            self.main_project_query = MainProject.objects.filter(plm_project = input_project)

    def update_status(self, status: MainProjectStatus):
        return self.main_project_query.update(status = status)

