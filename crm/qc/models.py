from django.db import models
from main.models import BaseModel
from django.conf import settings

class Month(models.IntegerChoices):
    JANUARY = 1, "January"
    FEBRUARY = 2, "February"
    MARCH = 3, "March"
    APRIL = 4, "April"
    MAY = 5, "May"
    JUNE = 6, "June"
    JULY = 7, "July"
    AUGUST = 8, "August"
    SEPTEMBER = 9, "September"
    OCTOBER = 10, "October"
    NOVEMBER = 11, "November"
    DECEMBER = 12, "December"

# Create your models here.
class PcmZCriterionPerAnalystMonth(BaseModel):
    month = models.PositiveSmallIntegerField(choices=Month.choices, null=True, blank=True)
    year = models.PositiveSmallIntegerField()
    analyst = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='z_criteria_analyst',
            verbose_name='Analyst',
        )

    relative_std_deviation_low = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    relative_std_deviation_medium = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    relative_std_deviation_high = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)

    def __str__(self):
        return str(self.year) + '-' + str(self.month) + '-' + self.analyst.username

class PlmTypeQCSample(models.IntegerChoices):
    Replicate = 1, 'Replicate'
    Duplicate = 2, 'Duplicate'

class PlmTypeAnalysisSample(models.IntegerChoices):
    PLM = 1, 'PLM'
    NOB = 2, 'NOB'
    TEM = 3, 'TEM'

class PlmReplicates(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(qc_type=PlmTypeQCSample.Replicate)
    
class PlmDuplicates(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(qc_type=PlmTypeQCSample.Duplicate)
  
class PlmQCReplicateDuplicateItem(BaseModel):
    qc_type = models.PositiveSmallIntegerField(choices=PlmTypeQCSample.choices, default=PlmTypeQCSample.Replicate)
    analysis_type = models.PositiveSmallIntegerField(choices=PlmTypeAnalysisSample.choices, default=PlmTypeAnalysisSample.PLM)
    project = models.ForeignKey('plm.PlmProject', on_delete=models.CASCADE, related_name='plm_project')
    original_sample = models.ForeignKey('plm.PlmSample', on_delete=models.CASCADE, related_name='original_sample')
    qc_sample = models.ForeignKey('plm.PlmSample', on_delete=models.CASCADE, related_name='qc_sample')
    analyst = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='analyst',
            verbose_name='Analyst',
        )
    reviewer = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='reviewer',                      # не показывать в формах
            verbose_name='Reviewer',
        )

    objects = models.Manager()
    plm_replicates = PlmReplicates()
    plm_duplicates = PlmDuplicates()

    @property
    def relative_diff(self):
        if self.original_sample.asb_percent is None or self.qc_sample.asb_percent is None:
            return 0

        denominator = (self.original_sample.asb_percent + self.qc_sample.asb_percent) / 2

        if denominator == 0:
            return 0

        return round(abs((self.original_sample.asb_percent - self.qc_sample.asb_percent) / denominator), 2)

    @property
    def pass_or_fail(self):
        if self.relative_diff > 1:
            return False
        else:
            return True

        
        