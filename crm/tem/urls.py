from django.contrib import admin
from django.urls import path, include
from tem import views

app_name = 'tem'

urlpatterns = [
    path('', views.tem_main_menu, name='tem_main_menu'), 
    path('original/grid-book', views.original_grid_book, name='original_grid_book'), 
    path('qc/grid-book', views.qc_grid_book, name='qc_grid_book'), 

    path('api/original/grid-book/get', views.api_get_original_grid_book_table, name='api_get_original_grid_book_table'),
    path('api/qc/grid-book/get', views.api_get_qc_grid_book_table, name='api_get_qc_grid_book_table'),
]


