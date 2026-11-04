from django.urls import path
app_name = 'pcm'

from . import views

urlpatterns = [
    path('projects', views.PcmMainProjectAPIList.as_view(), name='get_main_projects_table'),
    path('get-data-entry-table-options/', views.get_data_entry_options, name='get_data_entry_options'),
    path('data-entry-table/<int:id>/', views.PcmSampleDataEntry.as_view(), name='data_entry_table'),
    path('analysis-table/<int:id>/', views.PcmSampleAnalysis.as_view(), name='analysis_table'),
    path('analyst/<int:id>/', views.PcmAnalystAPI.as_view(), name='analyst'),
]

