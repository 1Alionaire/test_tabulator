from django.contrib import admin
from django.urls import path, include
from plm import views

app_name = 'plm'

urlpatterns = [
    path('', views.PLMTableView.as_view(), name='main'),
    path('detail/<int:id>/', views.UpdateProjectView.as_view(), name='plm_detail'),
    path('data-entry-upload-excel/<int:id>/', views.data_entry_upload_excel, name='data_entry_upload_excel'),
    path('api/plm-projects/get/', views.api_get_plm_projects_table, name='api_get_plm_projects_table'),
    # data-entry
    path('api/get-table-options/', views.api_get_table_options, name="api_get_table_options"),
    path('api/get-data-entry-table/get/<int:id>/', views.api_get_data_entry_table, name='api_get_data_entry_table'),
]


# path('api/get-table-options/', views.api_get_table_options, name="api_get_table_options"),
# 
# path('api/main-projects/update/', views.api_update_main_projects_table, name='api_update_main_projects_table'),

