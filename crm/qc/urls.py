from django.contrib import admin
from django.urls import path, include
from qc import views

app_name = 'qc'

urlpatterns = [
    path('user/plm/', views.UserPcmMenuView.as_view(), name='user_pcm_main'),
    path('user/plm/', views.UserPlmMenuView.as_view(), name='user_plm_main'),
    

    path('manager/pcm/', views.ManagerPcmMenuView.as_view(), name='manager_pcm_main'),
    path('manager/plm/', views.ManagerPlmMenuView.as_view(), name='manager_plm_main'),
    path('manager/plm/rep-dup/', views.ManagerPlmRepDupByAnalyst.as_view(), name='manager_plm_rep_dup_by_analyst'),
    path('manager/plm/rep-dup/info', views.ManagerPlmRepDupAllInfo.as_view(), name='manager_plm_rep_dup_all_info'),
        

]