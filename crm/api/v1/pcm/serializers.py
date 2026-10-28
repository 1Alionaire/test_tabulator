from rest_framework import serializers
from main.models import MainProject


class PcmMainProjectSerializer(serializers.ModelSerializer):
    pcm_project_id = serializers.IntegerField(source='pcm_project.id', read_only=True)

    class Meta:
        model = MainProject
        fields = '__all__'

