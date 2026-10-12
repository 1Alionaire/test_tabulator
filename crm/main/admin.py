from django.contrib import admin
from .models import MainProject
# Register your models here.

@admin.register(MainProject)
class MainProjectAdmin(admin.ModelAdmin):
    list_display = ('lab_id', 'project_name', 'company', 'project_type')
    list_filter = ('company', 'deleted', 'project_type')
    search_fields = ('lab_id', 'project_name', )
    ordering = ('-time_create', 'lab_id')
    list_per_page = 100

