from rest_framework import serializers
from qc.models import PcmZCriterionPerAnalystMonth

# Serializer for all PLM projects table
class UserPCMStdDeviationSerializer(serializers.ModelSerializer):
    # class Meta:
    #     model = PcmZCriterionPerAnalystMonth
    #     fields = '__all__'

    class Meta:
        model = PcmZCriterionPerAnalystMonth
        fields = (
            'id', 'analyst', 'year', 'month',
            'relative_std_deviation_low',
            'relative_std_deviation_medium',
            'relative_std_deviation_high',
        )
        read_only_fields = ('analyst',)


