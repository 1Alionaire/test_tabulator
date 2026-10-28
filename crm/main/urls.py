from django.contrib import admin
from django.urls import path, include
from main import views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

app_name = 'main'

urlpatterns = [
    path('', views.MainTableView.as_view(), name='main'),
    path('upload-coc/<int:id>/', views.UploadCOCView.as_view(), name='upload_coc_file'),
    path('redirect/<int:id>/', views.route_work, name='route_work'),
    path('api/get-table-options/', views.api_get_table_options, name="api_get_table_options"),
    path('api/main-projects/update/', views.api_update_main_projects_table, name='api_update_main_projects_table'),
]

