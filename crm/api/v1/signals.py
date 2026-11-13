from main.models import MainTypeAnalysis, MainProjectStatus, MainProject
from pcm.models import PcmProject, PcmSample
from plm.models import PlmProject, PlmSample, PlmSampleWeight, SampleMethod, SampleASbestosType
from tem.models import TEMGridRecord

import math
from django.db.models import Q, F

class MainProjectCreateSignal:
    def __init__(self, main_project):
        self.main_project = main_project

    def create_project(self):
        if self.main_project.project_type == MainTypeAnalysis.PCM:
            self._create_pcm_project()
        if self.main_project.project_type in [MainTypeAnalysis.Bulk, MainTypeAnalysis.BulkTEM, MainTypeAnalysis.EPT]:
            self._create_plm_project()

    def _create_pcm_project(self):
        created_pcm_project = PcmProject.objects.create(project=self.main_project) # Create PCM project entity
        # bulk create PCM samples
        PcmSample.objects.bulk_create([
            PcmSample(pcm_project=created_pcm_project,
                      row_number=( i +1),
                      lab_sample=str(self.main_project.lab_id) + '-' + str( i +1))
            for i in range(self.main_project.number_samples)
        ])

    def _create_plm_project(self):
        created_plm_project = PlmProject.objects.create(project=self.main_project)
        created_plm_project.save()
        amount_plm_samples = self.main_project.number_samples
        amount_nob_samples = self.main_project.nob_number_samples
        sum_samples = amount_plm_samples + amount_nob_samples
        PlmSample.objects.bulk_create([
            PlmSample(plm_project = created_plm_project,
                      row_number = (i + 1),
                      lab_sample = str(self.main_project.lab_id) + '-' + str(i + 1)) for i in range(sum_samples)
        ])
        if amount_nob_samples > 0:
            PlmSampleWeight.objects.bulk_create([
                PlmSampleWeight(plm_project = created_plm_project, version = 1)
                for i in range(amount_nob_samples)
            ])
            amount_blanks = math.ceil(amount_nob_samples /100)
            for i in range(amount_blanks):
                sample = PlmSample.objects.create(plm_project = created_plm_project,
                                                  row_number=( i +1000),
                                                  method = 3,
                                                  is_blank = True,
                                                  description = "Blank",
                                                  location = "Blank",
                                                  client_sample = "BL" + str(i + 1),
                                                  lab_sample = "BL" + str(i + 1),
                                                  version = 1)

                weight_item = PlmSampleWeight.objects.create(plm_project = created_plm_project,
                                                             client_sample = "BL" + str(i + 1),
                                                             version = 1)
                setattr(sample, 'weight', weight_item)
                sample.save()
                weight_item.save()
        else:
            weight_item = PlmSampleWeight.objects.create(plm_project=created_plm_project, version = 1)
            weight_item.save()

class MainProjectUpdateSignal:
    def __init__(self, input_project):
        if isinstance(input_project, PcmProject):
            self.main_project_query = MainProject.objects.filter(pcm_project = input_project)
        if isinstance(input_project, PlmProject):
            self.main_project_query = MainProject.objects.filter(plm_project = input_project)

    def update_status(self, status: MainProjectStatus):
        if status == MainProjectStatus.Done:
            return self.main_project_query.update(status = status, is_overdue=False, version=F("version") + 1,)
        else:
            return self.main_project_query.update(status = status, version=F("version") + 1,)

class MainProjectDeleteSignal:
    def __init__(self, main_project):
        self.main_project = main_project

    def delete_secondary_info(self):
        if self.main_project.project_type in [MainTypeAnalysis.Bulk, MainTypeAnalysis.BulkTEM, MainTypeAnalysis.EPT]:
            self.delete_plm_secondary_info()

    def delete_plm_secondary_info(self):
        deleted_plm_project = PlmProject.objects.get(project=self.main_project).id # Taking soft-deleted PLM project

        # release TEM grid slots held by deleted projects (bulk_update doesn't fire save signals)
        PlmSample.objects.filter(plm_project__project_id=deleted_plm_project).update(
            tem_grid_box=None,
            tem_grid_box_id_1=None,
            tem_grid_box_id_2=None,
            version=F("version") + 1,
        )

        TEMGridRecord.objects.filter(
            Q(plm_tem_project__project_id=deleted_plm_project)
            | Q(plm_tem_sample__plm_project__project_id=deleted_plm_project)
        ).update(plm_tem_project=None,
                 plm_tem_sample=None,
                 filled=False,
                 version=F("version") + 1,)
