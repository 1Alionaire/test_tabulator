from django.contrib import admin
from django.urls import path, include
from plm import views

app_name = 'plm'

urlpatterns = [
    # main table
    path('', views.PLMTableView.as_view(), name='main'),
    path('api/plm-projects/get/', views.api_get_plm_projects_table, name='api_get_plm_projects_table'),
    # project page
    path('detail/<int:id>/', views.UpdateProjectView.as_view(), name='plm_detail'),
    # options
    path('api/get-table-options/', views.api_get_table_options, name="api_get_table_options"),
    # data entry 
    path('api/plm-project/date-collect/update/<int:id>/', views.api_update_projects_date_collect, name = 'api_update_projects_date_collect'),
    path('data-entry-upload-excel/<int:id>/', views.data_entry_upload_excel, name='data_entry_upload_excel'),
    path('api/data-entry-table/get/<int:id>/', views.api_get_data_entry_table, name='api_get_data_entry_table'),
    path('api/data-entry-table/update/<int:id>/', views.api_update_data_entry_table, name='api_update_data_entry_table'),
    path('api/data-entry-table/replace-all/<int:id>/', views.api_replace_all_data_entry_table, name='api_replace_all_data_entry_table'),
    # weights 
    path('api/weight-table/get/<int:id>/', views.api_get_weight_table, name='api_get_weight_table'),
    path('api/weight-table/update/<int:id>/', views.api_update_weight_table, name='api_update_weight_table'),
    # Analysis 
    path('api/plm-project/update/<int:id>/', views.api_update_project_info, name='api_update_project_info'),
    path('api/nob-analysis-table/get/<int:id>/', views.api_get_nob_analysis_table, name='api_get_nob_analysis_table'),
    path('api/tem-analysis-table/get/<int:id>/', views.api_get_tem_analysis_table, name='api_get_tem_analysis_table'),
    path('api/analysis-table/update/<int:id>/', views.api_update_analysis_table, name='api_update_analysis_table'),
    # parse temperature
    path('api/temperature-get/<int:id>/', views.api_get_temperature, name = 'api_get_temperature'),
    #analyst API
    path('api/plm-project/analyst/get/<int:id>/', views.api_get_projects_analyst, name = 'api_get_projects_analyst'),
    path('api/plm-project/analyst/update/<int:id>/', views.api_update_projects_analyst, name = 'api_update_projects_analyst'),

    # QC
    path('api/qc/generate-samples/<int:id>/', views.api_generate_qc_samples, name = 'api_generate_qc_samples'),
    # generate report
    path('report/generate-report/<int:id>/', views.generate_plm_report, name='generate_plm_report'),
    path('report/generate-invoice/<int:id>/', views.generate_invoice, name='generate_invoice'),

]


