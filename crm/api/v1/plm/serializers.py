from rest_framework import serializers
from main.models import MainProject

# Serializer for all PCM projects table
class PlmMainProjectSerializer(serializers.ModelSerializer):
    plm_project_id = serializers.IntegerField(source='plm_project.id', read_only=True)

    class Meta:
        model = MainProject
        fields = '__all__'