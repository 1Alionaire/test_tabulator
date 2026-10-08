from django.contrib import admin
from .models import PcmProject, PcmSample, PcmSampleTimeTableRecord

@admin.register(PcmProject)
class PcmProjectAdmin(admin.ModelAdmin):
    list_display = ('lab_id', )
    search_fields = ('lab_id',)

    list_per_page = 10

@admin.register(PcmSample)
class PcmSampleAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_sample', 'lab_sample', 'row_number')
    search_fields = ('id', 'client_sample', 'lab_sample')

@admin.register(PcmSampleTimeTableRecord)
class PcmSampleTimeTableRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'year', 'month', 'day', 'row_number', 'project', 'start_time')
    search_fields = ('id', 'year', 'month', 'day')
    list_filter = ["year", "month", "day"]
