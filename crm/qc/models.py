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
