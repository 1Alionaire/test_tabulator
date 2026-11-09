from django.urls import path
app_name = 'pcm'

from . import views

urlpatterns = [
    # main table projects
    path('projects', views.PcmMainProjectAPIList.as_view(), name='get_main_projects_table'),
    # project form
    path('project-form/<int:id>/', views.PcmProjectInfoAPI.as_view(), name='project_form'),
    path('analyst/<int:id>/', views.PcmAnalystAPI.as_view(), name='analyst'),
    # tables
    path('get-data-entry-table-options/', views.get_data_entry_options, name='get_data_entry_options'),
    path('data-entry-table/<int:id>/', views.PcmSampleDataEntry.as_view(), name='data_entry_table'),
    path('analysis-table/<int:id>/', views.PcmSampleAnalysis.as_view(), name='analysis_table'),
    path('qc-table/<int:id>/', views.PcmSampleQc.as_view(), name='qc_table'),

]

