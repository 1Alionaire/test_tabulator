from django.urls import path
app_name = 'pcm'

from . import views

urlpatterns = [
    path('', views.PcmMainProjectAPIList.as_view(), name='get_main_projects_table'),
]