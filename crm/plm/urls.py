from django.contrib import admin
from django.urls import path, include
from plm import views

app_name = 'plm'

urlpatterns = [
    # main table
    path('', views.PLMTableView.as_view(), name='main'),
    # project page
    path('detail/<int:id>/', views.UpdateProjectView.as_view(), name='plm_detail'),
    # data entry
    path('data-entry-upload-excel/<int:id>/', views.data_entry_upload_excel, name='data_entry_upload_excel'),
    # QC
    path('api/qc/generate-samples/<int:id>/', views.api_generate_qc_samples, name = 'api_generate_qc_samples'),
    path('api/qc/complete/<int:id>/', views.api_complete_qc_process, name = 'api_complete_qc_process'),
    # generate report
    path('report/generate-report/<int:id>/', views.generate_plm_report, name='generate_plm_report'),
    path('report/generate-invoice/<int:id>/', views.generate_invoice, name='generate_invoice'),
]
