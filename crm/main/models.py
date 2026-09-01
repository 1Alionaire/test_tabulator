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

class TypeAnalysis(BaseModel):
    analysis_name = models.CharField(max_length=15)

    def __str__(self):
        return self.analysis_name

class TurnAroundTime(BaseModel):
    hour = models.PositiveIntegerField()
    label = models.CharField(max_length=10)

    def __str__(self):
        return self.label

class ProjectStatus(BaseModel):
    status_name = models.CharField(max_length=15)

    def __str__(self):
        return self.status_name

class ActiveProject(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)

class MainProject(BaseModel):
    lab_id = models.SlugField(max_length=20, unique=True) # project work number
    lab_id_sort = models.CharField(max_length=128, db_index=True, blank=True)
    date_registered = models.DateField(auto_now_add=False, default=timezone.now)  # date when project was registered
    time_registered = models.TimeField(auto_now_add=False, default=timezone.now) # time when project was registered
    company = models.ForeignKey('finance.Company', on_delete=models.CASCADE, related_name='companies') # client company
    project_name = models.CharField(max_length=100) # name of the project
    project_address = models.CharField(max_length=200) # address of the project
    sample_type = models.ForeignKey('main.TypeAnalysis', on_delete=models.CASCADE, related_name='project_sample_type')
    number_samples = models.PositiveIntegerField()
    turn_around_time = models.ForeignKey('main.TurnAroundTime', on_delete=models.CASCADE, related_name='project_turn_time')
    nob_number_samples = models.PositiveIntegerField(null=True, blank=True, default=0)
    technician = models.CharField(max_length=100, null=True, blank=True)
    status = models.ForeignKey('main.ProjectStatus', on_delete=models.CASCADE, related_name='project_status')
    comment = models.CharField(max_length=200, null=True, blank=True) # additional comments
    is_overdue = models.BooleanField(default=False)
    coc_file = models.FileField(upload_to='coc_files/', blank=True, null=True)
    deleted = models.BooleanField(blank=False, null=False, default=False,)

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

