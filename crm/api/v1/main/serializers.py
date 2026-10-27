from rest_framework import serializers
from main.models import MainProject

class MainProjectSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = MainProject
        fields = '__all__'
