from rest_framework import serializers
from main.models import MainProject

class MainProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainProject
        fields = ('__all__')

