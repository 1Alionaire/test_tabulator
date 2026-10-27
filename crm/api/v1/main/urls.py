from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

app_name = 'main'

from . import views

urlpatterns = [
    path('', views.MainProjectAPIList.as_view(), name='api_get_main_projects_table'),
]