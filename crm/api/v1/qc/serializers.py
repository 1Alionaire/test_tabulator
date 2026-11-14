from rest_framework import serializers
from qc.models import PcmZCriterionPerAnalystMonth, Month

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

    def validate(self, attrs):
        # one record per analyst + year + month: on create (POST) and on edit of year/month (PATCH)
        analyst = self.instance.analyst if self.instance else self.context['request'].user
        year = attrs.get('year', getattr(self.instance, 'year', None))
        month = attrs.get('month', getattr(self.instance, 'month', None))

        duplicates = PcmZCriterionPerAnalystMonth.objects.filter(analyst=analyst, year=year, month=month)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            month_label = Month(month).label if month else 'no month'
            raise serializers.ValidationError(f'Record for {month_label} {year} already exists')
        return attrs


