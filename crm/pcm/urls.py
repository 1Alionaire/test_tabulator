from django.urls import path
from pcm import views

app_name = 'pcm'

urlpatterns = [
    path('', views.PCMTableView.as_view(), name='main'), #render page
    path('api/pcm-projects/get/', views.api_get_pcm_projects_table, name='api_get_pcm_projects_table'), # getting all pcm projects
    path('detail/<int:id>/', views.UpdateProjectView.as_view(), name='pcm_detail'), #render single PCM project page
    path('api/get-table-options/', views.api_get_table_options, name='api_get_table_options'),
    # project info
    path('api/pcm-project/info/update/<int:id>/', views.api_update_project_info, name='api_update_project_info'),
    path('api/pcm-project/analyst/get/<int:id>/', views.api_get_projects_analyst, name='api_get_projects_analyst'),
    path('api/pcm-project/analyst/update/<int:id>/', views.api_update_projects_analyst, name='api_update_projects_analyst'),
    # data-entry
    path('api/data-entry-table/get/<int:id>/', views.api_get_data_entry_table, name='api_get_data_entry_table'),
    path('api/data-entry-table/update/<int:id>/', views.api_update_data_entry_table, name='api_update_data_entry_table'),
    # analysis
    path('api/analysis-table/get/<int:id>/', views.api_get_analysis_table, name='api_get_analysis_table'),
    path('api/analysis-table/update/<int:id>/', views.api_update_analysis_table, name='api_update_analysis_table'),
    # report
    path('report/generate/<int:id>/', views.generate_pcm_report, name='generate_pcm_report'),

    path('time-table/', views.PCMTimeTableByYearView.as_view(), name='time_table_by_year'),
    path('time-table/<int:year>/', views.PCMTimeTableByMonthView.as_view(), name='time_table_by_month'),
    path('time-table/<int:year>/<int:month>/<int:day>/', views.PCMTimeTableByDayView.as_view(), name='time_table_by_day'),

    path('api/time-table/get/<int:year>/<int:month>/<int:day>/', views.api_get_time_table, name='api_get_time_table'),
    path('api/time-table/update/<int:year>/<int:month>/<int:day>/', views.api_update_time_table, name='api_update_time_table'),

]
