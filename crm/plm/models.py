from django.db import models
from main.models import BaseModel
from django.utils import timezone
from django.conf import settings

def get_default_reviewer():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(username=settings.DEFAULT_REVIEWER_USERNAME).first()
    return user.pk if user else None

# Create your models here.
class PlmProject(BaseModel):
    project = models.OneToOneField('main.MainProject', on_delete=models.CASCADE, related_name='plm_project')
    date_collect = models.DateField(auto_now_add=False, default=timezone.now, blank=True, null=True)
    date_receive = models.DateField(auto_now_add=False, default=timezone.now, blank=True, null=True)
    date_prepare = models.DateField(auto_now_add=False, default=timezone.now, blank=True, null=True)
    date_analyze = models.DateField(auto_now_add=False, default=timezone.now, blank=True, null=True)
    date_report = models.DateField(auto_now_add=False, default=timezone.now, blank=True, null=True)
    date_review = models.DateField(auto_now_add=False, default=timezone.now, blank=True, null=True)
    prepared_by = models.CharField(max_length=30, blank=True)
    analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plm_analyst',
        verbose_name='Analyst',
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modifed_by',
        editable=False,                       # не показывать в формах
        verbose_name='Who update',
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_by',
        editable=False,                       # не показывать в формах
        verbose_name='Who update',
    )

    project_file = models.FileField(upload_to='plm_files/scan', blank=True, null=True)
    report_file = models.FileField(upload_to='plm_files/report', blank=True, null=True)
    plm_sample_count = models.PositiveIntegerField(default=0)
    nob_count = models.PositiveIntegerField(default=0)
    prep_nob_count = models.PositiveIntegerField(default=0)
    tem_count = models.PositiveIntegerField(default=0)
    qc_completed = models.BooleanField(default=False)

    @property
    def lab_id(self):
        return self.project.lab_id

class PlmSample(BaseModel):
    class SampleMorphology(models.IntegerChoices):
        Wavy = 1, 'W'
        Straight = 2, 'S'

    class SampleSignElong(models.IntegerChoices):
        POS = 1, 'POS'
        NEG = 2, 'NEG'

    class SampleExtincAngle(models.IntegerChoices):
        P = 1, 'P'
        O = 2, 'O'

    class SamplePleochColor(models.IntegerChoices):
        N = 1, 'N'
        Blue = 2, 'Blue'

    class SampleBirefringence(models.IntegerChoices):
        L = 1, 'L'
        M = 2, 'M'

    #general data
    plm_project = models.ForeignKey('plm.PlmProject', on_delete=models.CASCADE, related_name='plm_samples')
    homo_area = models.CharField(max_length=7, default='', blank=True)
    client_sample = models.CharField(max_length=20)
    lab_sample = models.CharField(max_length=25, default='', blank=True, null=True)
    description = models.CharField(max_length=100, default='')
    location = models.CharField(max_length=100, default='')
    method = models.CharField(max_length=8, blank=True, null=True)
    color = models.CharField(max_length=25, default='', blank=True)

    #analyze data
    weight = models.OneToOneField(
        "plm.PlmSampleWeight",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="sample",
    )

    analysis_temperature = models.PositiveIntegerField(default=23, null=True)
    texture = models.CharField(max_length=10, default='Non-Fibs', blank=True)
    homogeneity = models.CharField(max_length=2, blank=True)
    matx_reduc = models.CharField(max_length=2, blank=True)
    morphology = models.CharField(max_length=10, blank=True, default='')
    ri_alpha_oil = models.CharField(max_length=6, blank=True)
    ri_delta_oil = models.CharField(max_length=6, blank=True)
    sign_of_elongation = models.CharField(max_length=10, blank=True, default='')
    extinction_angle = models.CharField(max_length=10, blank=True, default='')
    pleochroism_color = models.CharField(max_length=10, blank=True, default='')
    birefringence = models.CharField(max_length=10, blank=True, default='')
    other_fiber = models.CharField(max_length=20, blank=True, default='')
    other_fiber_property = models.CharField(max_length=120, blank=True, default='', null=True)
    other_fiber_percent = models.DecimalField(max_digits=4, decimal_places=2, blank=True, default=0)

    # asb info
    asb_type = models.CharField(max_length=15, blank=True, null=True)
    asb_point_1 = models.PositiveIntegerField(default=0)
    asb_point_2 = models.PositiveIntegerField(default=0)
    asb_point_3 = models.PositiveIntegerField(default=0)
    asb_point_4 = models.PositiveIntegerField(default=0)
    asb_point_5 = models.PositiveIntegerField(default=0)
    asb_point_6 = models.PositiveIntegerField(default=0)
    asb_point_7 = models.PositiveIntegerField(default=0)
    asb_point_8 = models.PositiveIntegerField(default=0)
    asb_percent = models.DecimalField(max_digits=4, decimal_places=2, default=0, blank=True, null=True)

    tem_asb_type = models.CharField(max_length=15, blank=True, null=True)
    tem_asb_point = models.PositiveIntegerField(default=0)
    tem_asb_percent = models.DecimalField(max_digits=4, decimal_places=2, default=0, blank=True, null=True)

    
    def __str__(self):
        return self.lab_sample_id

# Weights
class PlmSampleWeight(BaseModel):
    client_sample = models.CharField(max_length=7, blank=True, null=True)
    w_crucible = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    w_crucible_with_sample = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    w_sample = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    w_sample_ashed = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    org = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    w_petri = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    w_petri_with_sample = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    residue = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    caco3 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f'Weights for {self.sample.lab_sample_id}'

