import math

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
    Abatement = 6, 'Abatement'
    AirQuality = 7, 'Air Quality Test'

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
    Note = 3, 'Note'

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
    time_analysis = models.TimeField(blank=True, null=True)
    segment_area = models.DecimalField(max_digits=6, decimal_places=5, default=Decimal("0.00785"))
    qc_accept_or_reject = models.PositiveSmallIntegerField(choices=SampleQCAcceptOrReject.choices, null=True, blank=True)

    def __str__(self):
        return self.lab_sample

    def average_flow_rate(self):
        if self.flow_rate_before is None or self.flow_rate_after is None:
            return None
        return (self.flow_rate_before + self.flow_rate_after) / 2

    def sampling_minutes(self):
        if self.time_in is None or self.time_out is None:
            return None
        minutes_in = self.time_in.hour * 60 + self.time_in.minute
        minutes_out = self.time_out.hour * 60 + self.time_out.minute
        return (minutes_out - minutes_in) % (24 * 60)  # sampling past midnight

    def calculate_sample_volume(self):
        # liters = average flow rate (L/min) * sampling time (min)
        minutes = self.sampling_minutes()
        flow_rate = self.average_flow_rate()
        if minutes is None or flow_rate is None:
            return None
        self.sample_volume =  PcmSample._round(flow_rate * minutes)

    def calculate_sample_fiber_per_mm(self, original=True):
        if original:
            if (self.amount_fibers is None) or (self.fields is None) or (self.segment_area is None):
                return None
            else:
                fiber_density = ((self.amount_fibers / self.fields) / self.segment_area)
        else:
            if (self.qc_amount_fibers is None) or (self.qc_fields is None) or (self.segment_area is None):
                return None
            else:
                fiber_density = ((self.qc_amount_fibers / self.qc_fields) / self.segment_area)

        return PcmSample._round(fiber_density, '0.01')


    def calculate_sample_fiber_per_cub_cm(self, original=True):
        if original:
            if (self.amount_fibers is None) or (self.fields is None) or (self.sample_volume is None):
                return None
            fiber_concentration = ((self.amount_fibers / self.fields) * 49) / self.sample_volume
        else:
            if (self.qc_amount_fibers is None) or (self.qc_fields is None) or (self.sample_volume is None):
                return None
            fiber_concentration = ((self.qc_amount_fibers / self.qc_fields) * 49) / self.sample_volume

        return PcmSample._round(fiber_concentration, '0.001')

    def calculate_qc_accept_or_reject(self, std_dev_low):
        # |√X₁ − √X₂| <= 2.77 × ((√X₁ + √X₂) / 2) × Sr -> Accept, otherwise Reject
        # X₁ = original F/mm², X₂ = QC F/mm²; no QC count or no Sr (empty or 0) -> no verdict
        if self.fiber_per_mm is None or not self.qc_fiber_per_mm or not std_dev_low:
            return None
        # float math in the same order as qcUpdateResult in pcm_qc.js, so browser and server agree
        sqrt_original = math.sqrt(float(self.fiber_per_mm))
        sqrt_qc = math.sqrt(float(self.qc_fiber_per_mm))
        limit = 2.77 * ((sqrt_original + sqrt_qc) / 2) * float(std_dev_low)

        if abs(sqrt_original - sqrt_qc) <= limit:
            self.qc_accept_or_reject = SampleQCAcceptOrReject.Accept
            return None

        self.qc_accept_or_reject = SampleQCAcceptOrReject.Reject
        return None


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

