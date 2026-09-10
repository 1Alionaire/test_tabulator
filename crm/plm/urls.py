from django.contrib import admin
from django.urls import path, include
from plm import views

app_name = 'plm'

urlpatterns = [
    path('', views.PLMTableView.as_view(), name='main'),
    path('api/plm-projects/get/', views.api_get_plm_projects_table, name='api_get_plm_projects_table'),
    path('detail/<int:id>/', views.UpdateProjectView.as_view(), name='plm_detail'),
    # data-entry
    path('data-entry-upload-excel/<int:id>/', views.data_entry_upload_excel, name='data_entry_upload_excel'),
    path('api/get-table-options/', views.api_get_table_options, name="api_get_table_options"),
    path('api/data-entry-table/get/<int:id>/', views.api_get_data_entry_table, name='api_get_data_entry_table'),
    path('api/data-entry-table/update/<int:id>/', views.api_update_data_entry_table, name='api_update_data_entry_table'),
    path('api/data-entry-table/replace-all/<int:id>/', views.api_replace_all_data_entry_table, name='api_replace_all_data_entry_table'),

    path('weight-upload-excel/<int:id>/', views.data_entry_upload_excel, name='data_entry_upload_excel'),
    path('api/weight-table/get/<int:id>/', views.api_get_weight_table, name='api_get_weight_table'),
]


