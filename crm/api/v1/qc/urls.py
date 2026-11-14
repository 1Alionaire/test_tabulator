from django.urls import path
app_name = 'qc'

from . import views

urlpatterns = [
    # main menu
    path('user/pcm/std-deviation/', views.UserPCMStdDeviation.as_view(), name='pcm_std_deviation'),
]
