from django.contrib import admin
from django.urls import path, include
from tem import views

app_name = 'tem'

urlpatterns = [
    path('', views.tem_main_menu, name='tem_main_menu')
]


