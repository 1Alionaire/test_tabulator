from django.contrib import admin
from django.urls import path, include
from finance import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_main_menu, name='finance_main_menu'),
    path('company/', views.CompanyTableView.as_view(), name='company_main'),
    path('api/company-price-table/get/', views.api_get_company_price_table, name='api_get_company_price_table'),
    path('api/company-price-table/update/', views.api_update_company_price_table, name='api_update_company_price_table'),
]