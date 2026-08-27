from django.contrib import admin
from django.urls import path, include
from main import views

app_name = 'main'

urlpatterns = [
    path('', views.main, name='main'),
    path('api/get-table-options/', views.api_get_table_options, name="api_get_table_options"),
    path('api/main-projects/get/', views.api_get_main_projects_table, name='api_get_main_projects_table'),
    path('api/main-projects/update/', views.api_update_main_projects_table, name='api_update_main_projects_table'),
]