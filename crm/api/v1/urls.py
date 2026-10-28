from django.urls import include, path

app_name = 'v1'

urlpatterns = [
    path('main/', include('api.v1.main.urls')),
    path('pcm/', include('api.v1.pcm.urls')),
]
