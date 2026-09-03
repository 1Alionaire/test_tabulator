from django.contrib import admin
from django.urls import path, include
from plm import views

app_name = 'plm'

urlpatterns = [
    path('', views.PLMTableView.as_view(), name='main'),
    path('detail/<int:id>/', views.UpdateProjectView.as_view(), name='plm_detail'),
    path('api/plm-projects/get/', views.api_get_plm_projects_table, name='api_get_plm_projects_table'),
]

