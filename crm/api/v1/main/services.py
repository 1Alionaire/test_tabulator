# services.py
from django.db import transaction
from django.utils import timezone

from finance.models import Company
from main.models import MainProject, MainProjectStatus
import django.utils

from api.v1.signals import MainProjectDeleteSignal, MainProjectCreateSignal
from utils.utils import generate_rand_string_4

class MainProjectError(Exception):
    pass

class MainProjectTableManager():
    def __init__(self, input_data, user):
        self.input_data = input_data
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])
        self.data_to_delete = input_data.get('deleted', [])
        self.now_moment = django.utils.timezone.now()
        self.user = user

    def table_update_processing(self) -> dict:
        result = {'status': 'ok'}
        with transaction.atomic():
            if bool(self.data_to_delete):
                result['deleted'] = self._delete_data()
            if bool(self.data_to_update):
                result['updated'] = self._update_data()
            if bool(self.data_to_create):
                result['created'] = self._create_data()
        return result

    def _delete_data(self):
        projects_to_delete = {project.id : project for project in
                                            MainProject.active_objects.select_for_update().filter(pk__in=self.data_to_delete)}

        for project in projects_to_delete.values():
            previous_lab_id = project.lab_id
            new_lab_id = previous_lab_id + '-del-' + generate_rand_string_4()
            setattr(project, 'lab_id', new_lab_id)
            setattr(project, 'lab_id_sort', MainProject._make_sort_key(new_lab_id))
            setattr(project, 'deleted', True)
            setattr(project, 'time_update', self.now_moment)
            MainProjectDeleteSignal(project).delete_secondary_info()

        return MainProject.active_objects.bulk_update(
            projects_to_delete.values(), sorted({'lab_id', 'lab_id_sort', 'deleted', 'time_update'})
        )

    def _update_data(self):
        work_data = self.data_to_update
        id_list = [element.get('id') for element in work_data]
        touched_fields = set()

        projects_to_update = {project.id: project for project in
                              MainProject.active_objects.select_for_update().filter(pk__in=id_list)}

        for record_row in work_data:
            project = projects_to_update[int(record_row.get('id'))]
            for name_field, value in record_row.items():
                if name_field != 'id':
                    setattr(project, name_field, value)
                    touched_fields.add(name_field)
                if name_field == 'lab_id':
                    new_lab_id_sort = MainProject._make_sort_key(value)
                    setattr(project, 'lab_id_sort', new_lab_id_sort)
                    touched_fields.add('lab_id_sort')
            setattr(project, 'time_update', self.now_moment)

        return MainProject.active_objects.bulk_update(
            projects_to_update.values(), sorted(touched_fields | {'time_update'})
        )

    def _create_data(self):
        saved_projects = []

        for data in self.data_to_create:
            lab_id_sort = MainProject._make_sort_key(data['lab_id'])
            saved_projects.append(MainProject(status=MainProjectStatus.New,
                                              time_create=self.now_moment,
                                              time_update=self.now_moment,
                                              deleted=False,
                                              login_by=self.user,
                                              lab_id_sort = lab_id_sort,
                                              **data))

        MainProject.objects.bulk_create(saved_projects)
        for project in saved_projects:
            MainProjectCreateSignal(project).create_project()

        return len(saved_projects)