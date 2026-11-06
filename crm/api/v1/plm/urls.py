from django.urls import path
app_name = 'plm'

from . import views

urlpatterns = [
    # main menu
    path('projects', views.PlmMainProjectAPIList.as_view(), name='get_main_projects_table'),
    # plm project urls
    path('analyst/<int:id>/', views.PlmAnalystAPI.as_view(), name='analyst'),
    path('temperature-get/<int:id>/', views.PlmTemperature.as_view(), name='temperature'),
    path('project-form/<int:id>/', views.PlmProjectInfoAPI.as_view(), name='project_form'),
    # table urls
    path('table-options/', views.get_table_options, name='get_table_options'),
    path('data-entry-table/<int:id>/', views.PlmSampleDataEntry.as_view(), name='data_entry_table'),
    path('weight-table/<int:id>/', views.PlmSampleWeightAPI.as_view(), name='weight_table'),
    path('plm-nob-analysis-table/<int:id>/', views.PlmNobAnalysisApi.as_view(), name='plm_nob_analysis_table'),
    path('plm-tem-analysis-table/<int:id>/', views.PlmTemAnalysisApi.as_view(), name='plm_tem_analysis_table'),

]

