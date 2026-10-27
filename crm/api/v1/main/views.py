from main.models import MainProject
from rest_framework import generics
from .serializers import MainProjectSerializer


class MainProjectAPIList(generics.ListCreateAPIView):
    queryset = MainProject.active_objects.all()
    serializer_class = MainProjectSerializer
