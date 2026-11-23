from rest_framework.exceptions import ValidationError

from tem.models import TEMGridRecord
from django.db import transaction
from utils.utils import generate_rand_string_4
from api.v1.utils import check_versions
from plm.models import PlmProject, PlmSample

class OriginalTEMBookManager():
    def __init__(self, input_data):
        self.input_data = input_data

    @transaction.atomic
    def assign_grids(self):
        for record in self.input_data:
            if PlmProject.objects.filter(project__lab_id=record['plm_tem_project']).exists():
                plm_project = PlmProject.objects.get(project__lab_id=record['plm_tem_project'])
                if (PlmSample.objects
                        .filter(plm_project=plm_project, client_sample=record['plm_tem_sample'])
                        .exists()):
                    grid_record = TEMGridRecord.objects.get(id=record['id'])
                    (PlmSample.objects
                     .filter(plm_project=plm_project, client_sample=record['plm_tem_sample'])
                     .update(tem_grid_box=grid_record.grid_box,
                             tem_grid_box_id_1=grid_record.grid_id_1,
                             tem_grid_box_id_2=grid_record.grid_id_2))
                    grid_record.plm_tem_project = record['plm_tem_project']
                    grid_record.plm_tem_sample = record['plm_tem_sample']
                    grid_record.save()
            else:
                raise ValidationError({'plm_tem_project': 'plm_tem_sample does not exist'})
        return len(self.input_data)
