from decimal import Decimal, ROUND_HALF_UP

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
        return super().get_queryset().filter(is_qc_sample=False, tem_is_qc_sample=False, is_blank=False)

# Create your models here.
class PlmProject(BaseModel):
    project = models.OneToOneField('main.MainProject', on_delete=models.CASCADE, related_name='plm_project')
    date_collect = models.DateField(auto_now_add=False, blank=True, null=True)
    date_receive = models.DateField(auto_now_add=False, default=timezone.now, blank=True, null=True)
    date_prepare = models.DateField(auto_now_add=False, blank=True, null=True)
    date_analyze = models.DateField(auto_now_add=False, blank=True, null=True)
    date_report = models.DateField(auto_now_add=False, blank=True, null=True)
    date_review = models.DateField(auto_now_add=False,  blank=True, null=True)
    preparer = models.ForeignKey( # prepared_by
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='preparer',
            verbose_name='Preparer',
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

    reviewer = models.ForeignKey( #reviewed_by
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
    plm_sample_count = models.PositiveSmallIntegerField(default=0)
    nob_count = models.PositiveSmallIntegerField(default=0)
    prep_nob_count = models.PositiveSmallIntegerField(default=0)
    tem_count = models.PositiveSmallIntegerField(default=0)
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
    NotSubmitted = 9, 'Not submitted'

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
    Cylindrical = 3, 'Cylindrical'
    Medula = 4, 'Medula'


class PlmSample(BaseModel):
    ASBESTOS_PARAMETERS = {
        2: {'morphology': 1, 'sign_of_elongation': 1, 'extinction_angle': 1, 'pleochroism_color': 1,
            'birefringence': 1},
        3: {'morphology': 2, 'sign_of_elongation': 1, 'extinction_angle': 1, 'pleochroism_color': 1,
            'birefringence': 2},
        4: {'morphology': 2, 'sign_of_elongation': 2, 'extinction_angle': 1, 'pleochroism_color': 2,
            'birefringence': 2},
        5: {'morphology': 2, 'sign_of_elongation': 1, 'extinction_angle': 1, 'pleochroism_color': 1,
            'birefringence': 2},
        6: {'morphology': 2, 'sign_of_elongation': 1, 'extinction_angle': 2, 'pleochroism_color': 1,
            'birefringence': 2},
        7: {'morphology': 2, 'sign_of_elongation': 1, 'extinction_angle': 2, 'pleochroism_color': 1,
            'birefringence': 2},
    };

    ASB_OIL_PARAMETERS = {2: {'delta': {19: '1.557', 20: '1.557',
                                        21: '1.556', 22: '1.556',
                                        23: '1.555', 24: '1.555',
                                        25: '1.554', 26: '1.554',
                                        27: '1.553'},
                              'alpha': {19: '1.552', 20: '1.552',
                                        21: '1.551', 22: '1.551',
                                        23: '1.550', 24: '1.550',
                                        25: '1.549', 26: '1.549',
                                        27: '1.548'}},
                          3: {'delta': {19: '1.700', 20: '1.700',
                                        21: '1.699', 22: '1.699',
                                        23: '1.698', 24: '1.698',
                                        25: '1.698', 26: '1.698',
                                        27: '1.697'},
                              'alpha': {19: '1.682', 20: '1.682',
                                        21: '1.681', 22: '1.681',
                                        23: '1.680', 24: '1.680',
                                        25: '1.679', 26: '1.679',
                                        27: '1.678'}},
                          5: {'delta': {19: '1.626', 20: '1.626',
                                        21: '1.625', 22: '1.625',
                                        23: '1.625', 24: '1.625',
                                        25: '1.624', 26: '1.624',
                                        27: '1.623'},
                              'alpha': {19: '1.611', 20: '1.611',
                                        21: '1.611', 22: '1.611',
                                        23: '1.610', 24: '1.610',
                                        25: '1.609', 26: '1.609',
                                        27: '1.608'}},
                          }

    ASB_TYPES_ARRAY = [SampleASbestosType.Chry,
                       SampleASbestosType.Amo,
                       SampleASbestosType.Croc,
                       SampleASbestosType.Anth,
                       SampleASbestosType.Trem,
                       SampleASbestosType.Act]

    #general data
    plm_project = models.ForeignKey('plm.PlmProject', on_delete=models.CASCADE, related_name='plm_samples')
    homo_area = models.CharField(max_length=7, default='', blank=True)
    row_number = models.PositiveSmallIntegerField(null=True, blank=True, default=1)
    layer = models.PositiveSmallIntegerField(null=True, blank=True, default=1)
    client_sample = models.CharField(max_length=20)
    lab_sample = models.CharField(max_length=25, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100,blank=True, null=True)
    method = models.PositiveSmallIntegerField(choices=SampleMethod.choices,default=SampleMethod.Sample1981)
    color = models.CharField(max_length=25, null=True, blank=True)
    is_qc_sample = models.BooleanField(default=False)

    #analyze data
    weight = models.OneToOneField(
        "plm.PlmSampleWeight",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="sample",
    )

    analysis_temperature = models.PositiveSmallIntegerField(default=23, null=True)
    texture = models.PositiveSmallIntegerField(choices=SampleTexture, default=SampleTexture.NonFibs, null=True, blank=True)

    morphology = models.PositiveSmallIntegerField(choices=SampleMorphology, null=True, blank=True)
    ri_alpha_oil = models.CharField(max_length=6, blank=True, null=True)
    ri_delta_oil = models.CharField(max_length=6, blank=True, null=True)
    sign_of_elongation = models.PositiveSmallIntegerField(choices=SampleSignElong, null=True, blank=True)
    extinction_angle = models.PositiveSmallIntegerField(choices=SampleExtincAngle, null=True, blank=True)
    pleochroism_color = models.PositiveSmallIntegerField(choices=SamplePleochColor, null=True, blank=True)
    birefringence = models.PositiveSmallIntegerField(choices=SampleBirefringence, null=True, blank=True)
    other_fiber = models.PositiveSmallIntegerField(choices=SampleOtherFiber, null=True, blank=True)
    other_fiber_property = models.PositiveSmallIntegerField(choices=SampleOtherFiberProperty, null=True, blank=True)
    other_fiber_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=0)

    # asb info
    asb_type = models.PositiveSmallIntegerField(choices=SampleASbestosType, default = SampleASbestosType.NAD, blank=True, null=True)
    asb_point_1 = models.PositiveSmallIntegerField(default=50)
    asb_point_2 = models.PositiveSmallIntegerField(default=50)
    asb_point_3 = models.PositiveSmallIntegerField(default=50)
    asb_point_4 = models.PositiveSmallIntegerField(default=50)
    asb_point_5 = models.PositiveSmallIntegerField(default=50)
    asb_point_6 = models.PositiveSmallIntegerField(default=50)
    asb_point_7 = models.PositiveSmallIntegerField(default=50)
    asb_point_8 = models.PositiveSmallIntegerField(default=50)
    asb_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)

    rest_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100, blank=True, null=True)
    is_blank = models.BooleanField(default=False)

    objects = models.Manager()
    original_samples = OriginalSamples()

    tem_asb_type_grid_1 = models.PositiveSmallIntegerField(choices=SampleASbestosType, null=True, blank=True)
    tem_asb_point_grid_1 = models.PositiveSmallIntegerField(default=0)
    tem_asb_percent_grid_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)

    tem_asb_type_grid_2 = models.PositiveSmallIntegerField(choices=SampleASbestosType, null=True, blank=True)
    tem_asb_point_grid_2 = models.PositiveSmallIntegerField(default=0)
    tem_asb_percent_grid_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)

    tem_asb_type_total = models.CharField(max_length=100, blank=True, null=True)
    tem_asb_percent_total = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)

    tem_microscope_alignment = models.CharField(max_length=7, blank=True, null=True)
    tem_eccentricity_adjusted = models.CharField(max_length=7, blank=True, null=True)
    tem_grid_pre_acceptability = models.CharField(max_length=7, blank=True, null=True)

    tem_grid_box = models.CharField(max_length=7, blank=True, null=True)
    tem_grid_box_id_1 = models.CharField(max_length=7, blank=True, null=True)
    tem_grid_box_id_2 = models.CharField(max_length=7, blank=True, null=True)
    tem_na_or_ps = models.CharField(max_length=3, blank=True, null=True)
    tem_is_qc_sample = models.BooleanField(default=False)

    def __str__(self):
        if self.lab_sample is None or self.lab_sample == "":
            return self.client_sample
        return self.lab_sample

    def is_original_sample(self):
        if self.is_qc_sample == False and self.tem_is_qc_sample == False and self.is_blank == False:
            return True
        else:
            return False

    @staticmethod
    def _round(value, places='0.01'):
        return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)

    def plm_nob_parameter_fill(self):
        self.ri_alpha_oil = self.ASB_OIL_PARAMETERS[self.asb_type]['alpha'][self.analysis_temperature]
        self.ri_delta_oil = self.ASB_OIL_PARAMETERS[self.asb_type]['delta'][self.analysis_temperature]
        self.morphology = self.ASBESTOS_PARAMETERS[self.asb_type]['morphology']
        self.sign_of_elongation = self.ASBESTOS_PARAMETERS[self.asb_type]['sign_of_elongation']
        self.extinction_angle = self.ASBESTOS_PARAMETERS[self.asb_type]['extinction_angle']
        self.pleochroism_color = self.ASBESTOS_PARAMETERS[self.asb_type]['pleochroism_color']
        self.birefringence = self.ASBESTOS_PARAMETERS[self.asb_type]['birefringence']

    def plm_nob_parameter_clean(self):
        self.ri_alpha_oil = None
        self.ri_delta_oil = None
        self.morphology = None
        self.sign_of_elongation = None
        self.extinction_angle = None
        self.pleochroism_color = None
        self.birefringence = None
        self.asb_percent = 0
        self.asb_point_1 = 50
        self.asb_point_2 = 50
        self.asb_point_3 = 50
        self.asb_point_4 = 50
        self.asb_point_5 = 50
        self.asb_point_6 = 50
        self.asb_point_7 = 50
        self.asb_point_8 = 50
        self.tem_na_or_ps = None

    def calculate_plm_nob_asb_percent(self):
        if self.asb_point_1 == 50 and self.asb_point_2 == 50 and self.asb_point_3 == 50 and self.asb_point_4 == 50:
            count_points = 0
            for point in [self.asb_point_5 + self.asb_point_6 + self.asb_point_7 + self.asb_point_8]:
                if point != 50:
                    count_points += 1
            self.asb_percent = PlmSample._round(Decimal(count_points / 4))
        else:
            sum_point = sum([self.asb_point_1, self.asb_point_2, self.asb_point_3, self.asb_point_4])
            if self.method == SampleMethod.Sample1981:
                self.asb_percent = PlmSample._round(400 / Decimal(sum_point))
            else:
                self.asb_percent = PlmSample._round((400 / Decimal(sum_point) * self.weight.residue) / 100)

    def calculate_tem_result(self):
        if self.weight is None:
            return
        if self.tem_asb_percent_grid_1 is None:
            self.tem_asb_percent_grid_1 = 0
        if self.tem_asb_percent_grid_2 is None:
            self.tem_asb_percent_grid_2 = 0

        self.tem_asb_percent_grid_1 = self._round((Decimal(self.tem_asb_point_grid_1) * self.weight.residue) / 100, '0.1' )
        self.tem_asb_percent_grid_2 = self._round((Decimal(self.tem_asb_point_grid_2) * self.weight.residue) / 100,'0.1')

        self.tem_asb_percent_total = PlmSample._round((self.tem_asb_percent_grid_1 + self.tem_asb_percent_grid_2) / 2, '0.1')

    def is_sample_tem_clean(self):
        if self.tem_asb_type_grid_1 is not None and self.tem_asb_type_grid_2 is not None:
            if self.tem_asb_type_grid_1 == SampleASbestosType.NAD and self.tem_asb_type_grid_2 == SampleASbestosType.NAD:
                return True
            else:
                return False
        else:
            return False

    def is_sample_tem_not_analyzed(self):
        if self.tem_asb_type_grid_1 is not None and self.tem_asb_type_grid_2 is not None:
            if self.tem_asb_type_grid_1 == SampleASbestosType.NotAnalyzed and self.tem_asb_type_grid_2 == SampleASbestosType.NotAnalyzed:
                return True
            else:
                return False
        else:
            return False

    def is_sample_tem_has_asbest(self):
        if self.tem_asb_type_grid_1 is not None and self.tem_asb_type_grid_2 is not None:
            if self.tem_asb_type_grid_1 in self.ASB_TYPES_ARRAY or self.tem_asb_type_grid_2 in self.ASB_TYPES_ARRAY:
                return True
            else:
                return False
        else:
            return False

    def write_tem_asb_result(self):
        if self.is_sample_tem_not_analyzed():
            self.tem_asb_type_total = SampleASbestosType.NotAnalyzed.label
            return
        if self.is_sample_tem_clean():
            self.tem_asb_type_total = SampleASbestosType.NAD.label
            return
        if self.is_sample_tem_has_asbest():
            if self.tem_asb_type_grid_1 == self.tem_asb_type_grid_2:
                self.tem_asb_type_total = SampleASbestosType(self.tem_asb_type_grid_1).label
                return
            else:
                if self.tem_asb_type_grid_1 in self.ASB_TYPES_ARRAY and self.tem_asb_type_grid_2 in self.ASB_TYPES_ARRAY:
                    self.tem_asb_type_total = SampleASbestosType(self.tem_asb_type_grid_1).label + '/' + SampleASbestosType(self.tem_asb_type_grid_2).label
                    return
                else:
                    if self.tem_asb_type_grid_1 in self.ASB_TYPES_ARRAY:
                        self.tem_asb_type_total = SampleASbestosType(self.tem_asb_type_grid_1).label
                    else:
                        self.tem_asb_type_total = SampleASbestosType(self.tem_asb_type_grid_2).label


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

