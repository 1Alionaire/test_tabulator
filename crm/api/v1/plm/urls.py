from django.urls import path
app_name = 'plm'

from . import views

urlpatterns = [
    path('projects', views.PlmMainProjectAPIList.as_view(), name='get_main_projects_table'),
    path('table-options/', views.get_table_options, name='get_table_options'),
    path('data-entry-table/<int:id>/', views.PlmSampleDataEntry.as_view(), name='data_entry_table'),
    path('weight-table/<int:id>/', views.PlmSampleWeightAPI.as_view(), name='weight_table'),
    # path('analysis-table/<int:id>/', views.PcmSampleAnalysis.as_view(), name='analysis_table'),
    path('analyst/<int:id>/', views.PlmAnalystAPI.as_view(), name='analyst'),
]

