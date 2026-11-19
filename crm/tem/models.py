from django.db import models
from main.models import BaseModel

# Create your models here.
class TEMGridRecord(BaseModel):
    position = models.PositiveIntegerField(default=1)
    year = models.PositiveSmallIntegerField()
    grid_box = models.PositiveIntegerField()
    grid_id_1 = models.CharField(max_length=5)
    grid_id_2 = models.CharField(max_length=5)

    plm_tem_project = models.ForeignKey(
        "plm.PlmProject",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="grid_tem_plm_project",
    )

    plm_tem_sample = models.OneToOneField(
        "plm.PlmSample",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="grid_tem_sample",
    )

    filled = models.BooleanField(default=False)
    qc = models.BooleanField(default=False)

class QCTEMGridRecord(BaseModel):
    all_grid_id = [('A1', 'B1'), ('C1', 'D1'), ('E1', 'A2'), ('B2', 'C2'), ('D2', 'E2'),
                   ('A3', 'B3'), ('C3', 'D3'), ('E3', 'A4'), ('B4', 'C4'), ('D4', 'E4'),
                   ('A5', 'B5'), ('C5', 'D5'), ('E5', 'A6'), ('B6', 'C6'), ('D6', 'E6'),
                   ('A7', 'B7'), ('C7', 'D7'), ('E7', 'A8'), ('B8', 'C8'), ('D8', 'E8'),
                   ('A9', 'B9'), ('C9', 'D9'), ('E9', 'A10'), ('B10', 'C10'), ('D10', 'E10')]

    year = models.PositiveSmallIntegerField()
    grid_box = models.PositiveIntegerField()
    grid_id_1 = models.CharField(max_length=5)
    grid_id_2 = models.CharField(max_length=5)

    plm_tem_project = models.ForeignKey(
        "plm.PlmProject",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="qc_grid_tem_plm_project",
    )

    plm_tem_sample = models.OneToOneField(
        "plm.PlmSample",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="qc_grid_tem_sample",
    )


    