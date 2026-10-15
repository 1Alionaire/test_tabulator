from django.contrib import admin

# Register your models here.
from .models import PcmZCriterionPerAnalystMonth, PlmQCReplicateDuplicateItem
# Register your models here.

@admin.register(PcmZCriterionPerAnalystMonth)
class PcmZCriterionPerAnalystMonthAdmin(admin.ModelAdmin):
    list_display = ('month', 'year', 'analyst', 
                    'relative_std_deviation_low', 
                    'relative_std_deviation_medium', 
                    'relative_std_deviation_high')
    search_fields = ('analyst',)

    list_per_page = 10

@admin.register(PlmQCReplicateDuplicateItem)
class PlmQCReplicateDuplicateItemAdmin(admin.ModelAdmin):
    list_display = ('qc_type',
                    'analysis_type',
                    'project', 
                    'original_sample', 
                    'qc_sample', 
                    'analyst', 
                    'reviewer', 
                    'relative_diff',
                    'pass_or_fail')
    search_fields = ('analyst', 'project', 'original_sample')

    list_per_page = 10
    
