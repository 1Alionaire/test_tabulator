from django.contrib import admin
from .models import TEMGridRecord, TEMGridQCRecord
# Register your models here.

@admin.register(TEMGridRecord)
class TEMGridRecordAdmin(admin.ModelAdmin):
    list_display = ('grid_box', 'grid_id_1', 'grid_id_2' )
    search_fields = ('grid_box', )
    list_filter = ['year', 'plm_tem_project__project__lab_id']

    list_per_page = 25

@admin.register(TEMGridQCRecord)
class TEMGridQCRecordAdmin(admin.ModelAdmin):
    list_display = ('grid_box', 'grid_id_1', 'grid_id_2' )
    search_fields = ('grid_box', )
    list_filter = ['year', 'plm_tem_project__project__lab_id']

    list_per_page = 25