from django.db import models
from django.db.models import Q

from main.models import BaseModel

# Create your models here.
class TEMGridRecord(BaseModel):
    all_grid_id = {1: ('A1', 'B1'),
                   2: ('C1', 'D1'),
                   3: ('E1', 'A2'),
                   4: ('B2', 'C2'),
                   5: ('D2', 'E2'),
                   6: ('A3', 'B3'),
                   7: ('C3', 'D3'),
                   8: ('E3', 'A4'),
                   9: ('B4', 'C4'),
                   10: ('D4', 'E4'),
                   11: ('A5', 'B5'),
                   12: ('C5', 'D5'),
                   13: ('E5', 'A6'),
                   14: ('B6', 'C6'),
                   15: ('D6', 'E6'),
                   16: ('A7', 'B7'),
                   17: ('C7', 'D7'),
                   18: ('E7', 'A8'),
                   19: ('B8', 'C8'),
                   20: ('D8', 'E8'),
                   21: ('A9', 'B9'),
                   22: ('C9', 'D9'),
                   23: ('E9', 'A10'),
                   24: ('B10', 'C10'),
                   25: ('D10', 'E10')}

    position = models.PositiveIntegerField(default=1)
    year = models.PositiveSmallIntegerField()
    grid_box = models.PositiveBigIntegerField()
    grid_id_1 = models.CharField(max_length=3)
    grid_id_2 = models.CharField(max_length=3)

    plm_tem_project = models.CharField(max_length = 15, null = True, blank = True)
    plm_tem_sample = models.CharField(max_length = 15, null = True, blank = True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["grid_box", "position"],
                name="uniq_grid_box_position",
                violation_error_message="This box already has record",
            ),
            # bonus: database check maximum value
            models.CheckConstraint(
                condition=Q(position__gte=1, position__lte=25),
                name="grid_position_1_25",
            ),
        ]
        indexes = [
            models.Index(fields=["-grid_box", "position"], name="grid_box_desc_pos_asc"),
        ]

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


    