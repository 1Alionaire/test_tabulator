from django.urls import path

app_name = 'tem'

from . import views

urlpatterns = [
    # main menu
    path('grid-book/qc/', views.QCTEMGridBook.as_view(), name='qc_grid_book_table'),
    path('grid-book/original/', views.TEMGridBook.as_view(), name='original_grid_book_table'),
    path('grid-book/original/create', views.create_grid_book, name='create_original_grid_book'),
]
