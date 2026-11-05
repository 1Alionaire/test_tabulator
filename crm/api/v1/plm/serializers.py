from rest_framework import serializers
from main.models import MainProject
from plm.models import PlmProject

# Serializer for all PLM projects table
class PlmMainProjectSerializer(serializers.ModelSerializer):
    plm_project_id = serializers.IntegerField(source='plm_project.id', read_only=True)

    class Meta:
        model = MainProject
        fields = '__all__'

class PlmAnalystSerializer(serializers.ModelSerializer):
    analyst_username = serializers.CharField(
        source="analyst.username",
        read_only=True,
        allow_null=True,
    )
    class Meta:
        model = PlmProject
        fields = ['analyst', "analyst_username"]