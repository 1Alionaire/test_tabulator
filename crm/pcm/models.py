from django.db import models
from main.models import BaseModel
from django.utils import timezone
from django.conf import settings
from qc.models import Month
from decimal import Decimal

class TypeSamplingPCM(models.IntegerChoices):
    Background = 1, 'Background / Pre-Abatement'
    During = 2, 'During'
    Ambient = 3, 'Ambient'
    Post = 4, 'Post'
    DuringAsFinals = 5, 'During-as-Finals'

class PcmProject(BaseModel):
    project = models.OneToOneField('main.MainProject', on_delete=models.CASCADE, related_name='pcm_project') #check
    date_collect = models.DateField(auto_now_add=False, default=timezone.now, blank=True) #check
    date_analyze = models.DateField(auto_now_add=False, default=timezone.now, blank=True) #check
    work_area = models.CharField(max_length=100, blank=True) #check
    analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pcm_analyst',
        verbose_name='Analyst',
    ) #check
    technician = models.CharField(max_length=50, null=True, blank=True)
    rotometer = models.CharField(max_length=50, null=True, blank=True)

    type_sampling = models.IntegerField(choices=TypeSamplingPCM, null=True, blank=True)

    z_criterion_record = models.ForeignKey('qc.PcmZCriterionPerAnalystMonth', on_delete=models.SET_NULL, null=True, blank=True, related_name='pcm_project')
    qc_completed = models.BooleanField(default=False)
    project_file = models.FileField(upload_to='pcm_files/scan', blank=True, null=True) #check
    report_file = models.FileField(upload_to='pcm_files/report', blank=True, null=True) #check
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pcm_reviewer',
        verbose_name='Reviewer',
    ) #check
    date_review = models.DateField(auto_now_add=False, default=timezone.now, blank=True) #check
    

    @property
    def lab_id(self):
        return self.project.lab_id

    def __str__(self):
        return self.project.lab_id

class SampleWorkArea(models.IntegerChoices):
    IWA = 1, 'IWA'
    OWA = 2, 'OWA'
    __empty__ = '—'

class SampleQCAcceptOrReject(models.IntegerChoices):
    Accept = 1, 'Accept'
    Reject = 2, 'Reject'

class PcmSample(BaseModel):
    pcm_project = models.ForeignKey('pcm.PcmProject', on_delete=models.CASCADE, related_name='pcm_samples')
    client_sample = models.CharField(max_length=20, default='', null=True, blank=True)
    row_number = models.PositiveSmallIntegerField(null=True, blank=True, default=1)
    lab_sample = models.CharField(max_length=25, default='', null=True, blank=True)
    iwa_owa = models.PositiveSmallIntegerField(choices=SampleWorkArea.choices, null=True, blank=True) 
    location = models.CharField(max_length=100, default='', null=True, blank=True)
    time_in = models.TimeField(auto_now_add=False, null=True, blank=True)
    time_out = models.TimeField(auto_now_add=False, null=True, blank=True)
    flow_rate_before = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    flow_rate_after = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    sample_volume = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    amount_fibers = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)
    fields = models.PositiveSmallIntegerField(default=100)
    fiber_per_cub_cm = models.DecimalField(max_digits=6, decimal_places=3, blank=True, null=True)
    fiber_per_mm = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    qc_amount_fibers = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)
    qc_fields = models.PositiveSmallIntegerField(default=100)
    qc_fiber_per_cub_cm = models.DecimalField(max_digits=6, decimal_places=3, blank=True, null=True)
    qc_fiber_per_mm = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    time_analysis = models.TimeField(auto_now_add=False, default=timezone.now)
    segment_area = models.DecimalField(max_digits=6, decimal_places=5, default=Decimal("0.00785"))
    qc_accept_or_reject = models.PositiveSmallIntegerField(choices=SampleQCAcceptOrReject.choices, null=True, blank=True)

class PcmSampleTimeTableRecord(BaseModel):
    analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_table_analyst',
        verbose_name='Analyst',
    ) #check
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    month = models.PositiveSmallIntegerField(choices=Month.choices, null=True, blank=True)
    day = models.PositiveSmallIntegerField(null=True, blank=True)
    row_number = models.PositiveSmallIntegerField(null=True, blank=True)
    project = models.CharField(max_length=40, null=True, blank=True)
    start_time = models.CharField(max_length=7, null=True, blank=True)
    end_time = models.CharField(max_length=7, null=True, blank=True)

