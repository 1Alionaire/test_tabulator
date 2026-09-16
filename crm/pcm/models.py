from django.db import models
from main.models import BaseModel
from django.utils import timezone
from django.conf import settings

class TypeSamplingPCM(models.IntegerChoices):
    Background = 1, 'Background / Pre-Abatement'
    During = 2, 'During'
    Ambient = 3, 'Ambient'
    Post = 4, 'Post'
    DuringAsFinals = 5, 'During-as-Finals'

class WorkArea(models.IntegerChoices):
    IWA = 1, 'IWA'
    OWA = 2, 'OWA'

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
        related_name='analyst',
        verbose_name='Analyst',
    ) #check
    technician = models.CharField(max_length=50, null=True, blank=True)
    rotometer = models.CharField(max_length=50, null=True, blank=True)

    type_sampling = models.IntegerField(choices=TypeSamplingPCM, null=True, blank=True)

    relative_std_deviation_low = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    relative_std_deviation_medium = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    relative_std_deviation_high = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    
    qc_completed = models.BooleanField(default=False)
    project_file = models.FileField(upload_to='pcm_files/scan', blank=True, null=True) #check
    report_file = models.FileField(upload_to='pcm_files/report', blank=True, null=True) #check

    def __str__(self):
        return self.pcm_lab_id.lab_id

class PcmSample(BaseModel):
    pcm_project = models.ForeignKey('pcm.PcmProject', on_delete=models.CASCADE, related_name='pcm_samples')
    client_sample_id = models.CharField(max_length=20, default='', null=True, blank=True)
    lab_sample_id = models.CharField(max_length=25, default='', null=True, blank=True)
    iwa_owa = models.CharField(max_length=4, default='', null=True, blank=True) #models.IntegerField(choices=WorkArea.choices, default=WorkArea.NoArea)
    location = models.CharField(max_length=100, default='', null=True, blank=True)
    time_in = models.TimeField(auto_now_add=False, null=True, blank=True)
    time_out = models.TimeField(auto_now_add=False, null=True, blank=True)
    flow_rate_before = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    flow_rate_after = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    sample_volume = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    amount_fibers = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)
    fields = models.IntegerField(default=100)
    fiber_per_cub_centimeter = models.DecimalField(max_digits=6, decimal_places=3, blank=True, null=True)
    fiber_per_mm = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)