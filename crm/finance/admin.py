from django.contrib import admin
from .models import Company
# Register your models here.

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'representative' )
    list_filter = ('name', 'representative', )
    search_fields = ('name', 'representative')
    ordering = ('name', 'representative')
    list_per_page = 10