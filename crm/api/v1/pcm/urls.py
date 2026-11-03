from django.urls import path
app_name = 'pcm'

from . import views

urlpatterns = [
    path('projects', views.PcmMainProjectAPIList.as_view(), name='get_main_projects_table'),

    path('get-data-entry-table-options/', views.get_data_entry_options, name='get_data_entry_options'),
    # path('data-entry-table/get/<int:id>/', views.api_get_data_entry_table, name='api_get_data_entry_table'),
]