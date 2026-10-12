from django.contrib import admin

# Register your models here.
from .models import PcmZCriterionPerAnalystMonth
# Register your models here.

@admin.register(PcmZCriterionPerAnalystMonth)
class PcmZCriterionPerAnalystMonthAdmin(admin.ModelAdmin):
    list_display = ('month', 'year', 'analyst', 
                    'relative_std_deviation_low', 
                    'relative_std_deviation_medium', 
                    'relative_std_deviation_high')
    search_fields = ('analyst',)

    list_per_page = 10


