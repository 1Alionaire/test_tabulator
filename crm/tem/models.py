from django.db import models
from main.models import BaseModel

# Create your models here.
class TEMGridRecord(BaseModel):
    position = models.PositiveIntegerField(default=1)
    year = models.PositiveIntegerField()
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

# Create your models here.
class TEMGridQCRecord(TEMGridRecord):
    pass

    