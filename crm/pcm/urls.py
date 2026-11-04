from django.urls import path
from pcm import views

app_name = 'pcm'

urlpatterns = [
    path('', views.PCMTableView.as_view(), name='main'), #render page
    path('project/<int:id>/', views.UpdateProjectView.as_view(), name='pcm_project'), #render single PCM project page
    # project info
    path('api/pcm-project/info/update/<int:id>/', views.api_update_project_info, name='api_update_project_info'),
    # report
    path('report/generate/<int:id>/', views.generate_pcm_report, name='generate_pcm_report'),
    #time table
    path('time-table/', views.PCMTimeTableByYearView.as_view(), name='time_table_by_year'),
    path('time-table/<int:year>/', views.PCMTimeTableByMonthView.as_view(), name='time_table_by_month'),
    path('time-table/<int:year>/<int:month>/<int:day>/', views.PCMTimeTableByDayView.as_view(), name='time_table_by_day'),

    path('api/time-table/get/<int:year>/<int:month>/<int:day>/', views.api_get_time_table, name='api_get_time_table'),
    path('api/time-table/update/<int:year>/<int:month>/<int:day>/', views.api_update_time_table, name='api_update_time_table'),

]
