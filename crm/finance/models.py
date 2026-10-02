from django.db import models
from main.models import BaseModel
from django.utils.text import slugify

# Create your models here.
class Company(BaseModel):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True, editable=False)
    representative = models.CharField(max_length=100, blank=True, null=True)
    #Prices
    pcm_price = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True, default=0)
    plm_price = models.DecimalField(decimal_places=2, max_digits=7, null=True, blank=True, default=0)
    nob_price = models.DecimalField(decimal_places=2, max_digits=7, null=True, blank=True, default=0)
    prep_nob_price = models.DecimalField(decimal_places=2, max_digits=7, null=True, blank=True, default=0)
    tem_price = models.DecimalField(decimal_places=2, max_digits=7, null=True, blank=True, default=0)
    air_tem_price = models.DecimalField(decimal_places=2, max_digits=7, null=True, blank=True, default=0)
    lead_wipe_price = models.DecimalField(decimal_places=2, max_digits=7, null=True, blank=True, default=0)
    lead_air_price = models.DecimalField(decimal_places=2, max_digits=7, null=True, blank=True, default=0)
    vermi_price = models.DecimalField(decimal_places=2, max_digits=7, null=True, blank=True, default=0)
    mold_price = models.DecimalField(decimal_places=2, max_digits=7, null=True, blank=True, default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name