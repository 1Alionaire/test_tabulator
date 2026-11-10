from django.urls import path
from main import views


app_name = 'main'

urlpatterns = [
    path('', views.MainTableView.as_view(), name='main'),
    path('upload-coc/<int:id>/', views.UploadCOCView.as_view(), name='upload_coc_file'),
    path('redirect/<int:id>/', views.route_work, name='route_work'),
]

