from django.urls import path
app_name = 'finance'

from . import views

urlpatterns = [
    path('company-price-table', views.CompanyPriceTableView.as_view(), name='company_table'),
]