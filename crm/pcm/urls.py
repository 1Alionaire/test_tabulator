from django.contrib import admin
from django.urls import path, include
from pcm import views

app_name = 'pсm'

urlpatterns = [
    path('', views.test_function, name='main')
]


