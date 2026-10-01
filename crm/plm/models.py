from django.db import models
from main.models import BaseModel
from django.utils import timezone
from django.conf import settings

def get_default_reviewer():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(username=settings.DEFAULT_REVIEWER_USERNAME).first()
    return user.pk if user else None

class OriginalSamples(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_qc_sample=False, is_tem_qc_sample=False, is_blank=False)

# Create your models here.
class PlmProject(BaseModel):
    project = models.OneToOneField('main.MainProject', on_delete=models.CASCADE, related_name='plm_project')
    date_collect = models.DateField(auto_now_add=False, blank=True, null=True)
    date_receive = models.DateField(auto_now_add=False, default=timezone.now, blank=True, null=True)
    date_prepare = models.DateField(auto_now_add=False, blank=True, null=True)
    date_analyze = models.DateField(auto_now_add=False, blank=True, null=True)
    date_report = models.DateField(auto_now_add=False, blank=True, null=True)
    date_review = models.DateField(auto_now_add=False,  blank=True, null=True)
    prepared_by = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='prepared_by',
            verbose_name='Prepare',
        )
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
        related_name='reviewed_by',                      # не показывать в формах
        verbose_name='Who reviewed',
    )

    coc_file = models.FileField(upload_to='plm_files/coc', blank=True, null=True)
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

    # @property
    def __str__(self):
        return self.project.lab_id

class SampleMethod(models.IntegerChoices):
    Sample1981 = 1, '198.1'
    Sample1984 = 2, '198.4'
    Sample1986 = 3, '198.6'
    Sample1994 = 4, '199.4'

class SampleASbestosType(models.IntegerChoices):
    NAD = 1, 'NAD'
    Chry = 2, 'Chrysotile'
    Amo = 3, 'Amosite'
    Croc = 4, 'Crocidolite'
    Anth = 5, 'Anthophillite'
    Trem = 6, 'Tremolite'
    Act = 7, 'Actinolite'
    NotAnalyzed = 8, 'Not analyzed'

class SampleTexture(models.IntegerChoices):
    NonFibs = 1, 'Non-Fibs'
    Fibrous = 2, 'Fibrous'
    Mixed = 3, 'Mixed'
    NotApplicable = 4, 'N/A'

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

class SampleOtherFiber(models.IntegerChoices):
    FiberGlass = 1, 'FiberGlass'
    Cellulose = 2, 'Cellulose'
    Synthetic = 3, 'Synthetic'
    HorseHair = 4, 'HorseHair'
    MineralWool = 5, 'MineralWool'

class SampleOtherFiberProperty(models.IntegerChoices):
    Isotropic = 1, 'Isotropic'
    Ribbon = 2, 'Ribbon'
    Medula = 3, 'Medula'
    Cylindrical = 4, 'Cylindrical'

class PlmSample(BaseModel):
    # status = models.IntegerField(choices=StatusWork.choices, default=StatusWork.NEW, blank=True, null=True)
    #general data
    plm_project = models.ForeignKey('plm.PlmProject', on_delete=models.CASCADE, related_name='plm_samples')
    homo_area = models.CharField(max_length=7, default='', blank=True)
    row_number = models.PositiveIntegerField(null=True, blank=True, default=1)
    layer = models.PositiveIntegerField(null=True, blank=True, default=1)
    client_sample = models.CharField(max_length=20)
    lab_sample = models.CharField(max_length=25, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100,blank=True, null=True)
    method = models.IntegerField(choices=SampleMethod.choices,default=SampleMethod.Sample1981)
    color = models.CharField(max_length=25, null=True, blank=True)
    is_qc_sample = models.BooleanField(default=False)

    #analyze data
    weight = models.OneToOneField(
        "plm.PlmSampleWeight",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="sample",
    )

    analysis_temperature = models.PositiveIntegerField(default=23, null=True)
    texture = models.IntegerField(choices=SampleTexture, default=SampleTexture.NonFibs, null=True, blank=True)

    morphology = models.IntegerField(choices=SampleMorphology, null=True, blank=True)
    ri_alpha_oil = models.CharField(max_length=6, blank=True, null=True)
    ri_delta_oil = models.CharField(max_length=6, blank=True, null=True)
    sign_of_elongation = models.IntegerField(choices=SampleSignElong, null=True, blank=True)
    extinction_angle = models.IntegerField(choices=SampleExtincAngle, null=True, blank=True)
    pleochroism_color = models.IntegerField(choices=SamplePleochColor, null=True, blank=True)
    birefringence = models.IntegerField(choices=SampleBirefringence, null=True, blank=True)
    other_fiber = models.IntegerField(choices=SampleOtherFiber, null=True, blank=True)
    other_fiber_property = models.IntegerField(choices=SampleOtherFiberProperty, null=True, blank=True)
    other_fiber_percent = models.DecimalField(max_digits=4, decimal_places=2, blank=True, default=0)

    # asb info
    asb_type = models.IntegerField(choices=SampleASbestosType, default = SampleASbestosType.NAD , null=True, blank=True)
    asb_point_1 = models.PositiveIntegerField(default=50)
    asb_point_2 = models.PositiveIntegerField(default=50)
    asb_point_3 = models.PositiveIntegerField(default=50)
    asb_point_4 = models.PositiveIntegerField(default=50)
    asb_point_5 = models.PositiveIntegerField(default=50)
    asb_point_6 = models.PositiveIntegerField(default=50)
    asb_point_7 = models.PositiveIntegerField(default=50)
    asb_point_8 = models.PositiveIntegerField(default=50)
    asb_percent = models.DecimalField(max_digits=4, decimal_places=2, default=0, blank=True, null=True)

    rest_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100, blank=True, null=True)

    tem_asb_type = models.IntegerField(choices=SampleASbestosType, default = SampleASbestosType.NAD, null=True, blank=True)
    tem_asb_point = models.PositiveIntegerField(default=0)
    tem_asb_percent = models.DecimalField(max_digits=4, decimal_places=2, default=0, blank=True, null=True)

    tem_microscope_alignment = models.CharField(max_length=7, default = 'Y', blank=True, null=True)
    tem_eccentricity_adjusted = models.CharField(max_length=7, default = 'Y', blank=True, null=True)
    tem_grid_pre_acceptability = models.CharField(max_length=7, default = 'Y', blank=True, null=True)

    tem_grid_box = models.CharField(max_length=7, blank=True, null=True)
    tem_grid_box_id_1 = models.CharField(max_length=7, blank=True, null=True)
    tem_grid_box_id_2 = models.CharField(max_length=7, blank=True, null=True)
    tem_na_or_ps = models.CharField(max_length=3, blank=True, null=True)
    is_tem_qc_sample = models.BooleanField(default=False)

    is_blank = models.BooleanField(default=False)

    objects = models.Manager()
    original_samples = OriginalSamples()

    def __str__(self):
        return self.lab_sample

# Weights
class PlmSampleWeight(BaseModel):
    plm_project = models.ForeignKey('plm.PlmProject', on_delete=models.CASCADE, related_name='plm_weights', null=True, blank=True)
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
        if self.client_sample:
            return self.client_sample
        else:
            return str(self.id)

