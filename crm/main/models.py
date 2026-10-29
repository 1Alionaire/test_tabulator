from django.db import models

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
import re

# Create your models here.
class BaseModel(models.Model):
    time_create = models.DateTimeField(auto_now_add=True,  verbose_name='Time create')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Time update')

    class Meta:
        abstract = True

class MainTypeAnalysis(models.IntegerChoices):
    PCM = 1, 'PCM'
    Bulk = 2, 'Bulk'
    BulkTEM = 3, 'Bulk-TEM'
    TEM = 4, 'TEM'
    AirTEM = 5, 'Air-TEM'
    LeadWipe = 6, 'Lead-Wipe'
    LeadWater = 7, 'Lead-Water'
    LeadPaint = 8, 'Lead-Paint'
    LeadAir = 9, 'Lead-Air'
    MoldTape = 10, 'Mold-Tape'
    MoldAir = 11, 'Mold-Air'
    MoldSwab = 12, 'Mold-Swab'
    Vermiculite = 13, 'Vermiculite'

class MainTurnAroundTime(models.IntegerChoices):
    Hour1 = 1, 'Rush'
    Hour3 = 3, '3 Hours'
    Hour6 = 6, '6 Hours'
    Hour12 = 12, '12 Hours'
    Hour24 = 24, '24 Hours'
    Hour48 = 48, '48 Hours'
    Hour72 = 72, '72 Hours'

class MainProjectStatus(models.IntegerChoices):
    New = 1, 'New'
    InProcess = 2, 'In Process'
    Overdue = 3, 'Overdue'
    Done = 4, 'Done'


class ActiveProject(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)

class MainProject(BaseModel):
    lab_id = models.SlugField(max_length=20, unique=True) # project work number
    lab_id_sort = models.CharField(max_length=128, db_index=True, blank=True)
    date_registered = models.DateField(auto_now_add=False, default=timezone.now)  # date when project was registered
    time_registered = models.TimeField(auto_now_add=False, default=timezone.now) # time when project was registered
    company = models.ForeignKey('finance.Company', on_delete=models.PROTECT, related_name='companies') # client company
    project_number = models.CharField(max_length=100)  # name of the project
    project_name = models.CharField(max_length=100) # name of the project
    project_address = models.CharField(max_length=200) # address of the project
    project_type = models.PositiveSmallIntegerField(choices=MainTypeAnalysis.choices, blank=False, null=False)
    number_samples = models.PositiveSmallIntegerField()
    turn_around_time = models.PositiveSmallIntegerField(choices=MainTurnAroundTime.choices, blank=False, null=False)
    nob_number_samples = models.PositiveSmallIntegerField(null=True, blank=True, default=0)
    technician = models.CharField(max_length=100, null=True, blank=True)
    status = models.PositiveSmallIntegerField(choices=MainProjectStatus.choices, blank=False, null=False)
    comment = models.CharField(max_length=200, null=True, blank=True) # additional comments
    is_overdue = models.BooleanField(default=False)
    coc_file = models.FileField(upload_to='coc_files/', blank=True, null=True)
    deleted = models.BooleanField(blank=False, null=False, default=False,)
    login_by = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='login_by')

    objects = models.Manager()
    active_objects = ActiveProject()
    
    def __str__(self):
        return super().__str__() + f' - {self.lab_id}'
    
    def save(self, *args, **kwargs):
        self.lab_id_sort = self._make_sort_key(self.lab_id)
        super().save(*args, **kwargs)

    @staticmethod
    def _make_sort_key(value: str) -> str:
        # каждое число паддим до 8 символов
        return re.sub(r'\d+', lambda m: m.group().zfill(8), value or '')

    @property
    def has_coc(self) -> bool:
        return bool(self.coc_file)

