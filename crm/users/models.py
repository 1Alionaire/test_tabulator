from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    pcm_microscope = models.CharField(max_length=30, null=True, blank=True)
    plm_microscope = models.CharField(max_length=30, null=True, blank=True)
    plm_scales = models.CharField(max_length=30, null=True, blank=True)

