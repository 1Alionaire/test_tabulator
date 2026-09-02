from django.contrib import admin
from .models import PlmProject, PlmSample, PlmSampleWeight
# Register your models here.

@admin.register(PlmProject)
class PlmProjectAdmin(admin.ModelAdmin):
    list_display = ('lab_id', )
    search_fields = ('lab_id',)

    list_per_page = 10

@admin.register(PlmSample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_sample', 'lab_sample')
    search_fields = ('id', 'client_sample', 'lab_sample')

@admin.register(PlmSampleWeight)
class PlmSampleWeightAdmin(admin.ModelAdmin):
    list_display = ('client_sample',)
    search_fields = ('client_sample',)