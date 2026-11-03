from rest_framework import serializers
from main.models import MainProject
from pcm.models import PcmProject, PcmSample

class PcmMainProjectSerializer(serializers.ModelSerializer):
    pcm_project_id = serializers.IntegerField(source='pcm_project.id', read_only=True)

    class Meta:
        model = MainProject
        fields = '__all__'

class PcmDataEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PcmSample
        fields = ['id', 'pcm_project', 'client_sample', 'row_number', 'lab_sample', 'iwa_owa',
                  'location', 'time_in', 'time_out', 'flow_rate_before', 'flow_rate_after',
                  'sample_volume']