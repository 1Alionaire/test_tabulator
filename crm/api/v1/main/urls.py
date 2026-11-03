from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

app_name = 'main'

from . import views

urlpatterns = [
    path('get-projects-table-options/', views.get_main_project_table_options, name="get_main_project_table_options"),
    path('projects', views.MainProjectAPIList.as_view(), name='get_main_projects_table'),
    path('projects-update', views.MainProjectChangesView.as_view(), name='update_main_projects_table'),
]

