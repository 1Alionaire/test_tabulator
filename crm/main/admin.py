from django.contrib import admin
from .models import MainProject, TypeAnalysis, TurnAroundTime, ProjectStatus
# Register your models here.

@admin.register(MainProject)
class MainProjectAdmin(admin.ModelAdmin):
    list_display = ('lab_id', 'project_name', 'company')
    list_filter = ('company', )
    search_fields = ('lab_id', 'project_name')
    ordering = ('-time_create', 'lab_id')
    list_per_page = 10

@admin.register(TypeAnalysis)
class TypeAnalysisAdmin(admin.ModelAdmin):
    list_display = ('analysis_name',)
    list_filter = ('analysis_name', )
    search_fields = ('analysis_name', )
    ordering = ('analysis_name', )
    list_per_page = 10

@admin.register(TurnAroundTime)
class TypeAnalysisAdmin(admin.ModelAdmin):
    list_display = ('label',)
    list_filter = ('label', )
    search_fields = ('label', )
    ordering = ('label', )
    list_per_page = 10

@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    list_display = ('status_name',)
    list_filter = ('status_name', )
    search_fields = ('status_name', )
    ordering = ('status_name', )
    list_per_page = 10