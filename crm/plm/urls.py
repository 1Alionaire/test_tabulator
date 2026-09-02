from django.contrib import admin
from django.urls import path, include
from plm import views

app_name = 'plm'

urlpatterns = [
    path('', views.PLMTableView.as_view(), name='plm_main'),
]

