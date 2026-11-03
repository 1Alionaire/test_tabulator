from rest_framework import serializers
from main.models import MainProject
from pcm.models import PcmProject, PcmSample

PCM_DATA_ENTRY_CREATE_FIELDS = ['client_sample', 'row_number', 'lab_sample', 'iwa_owa',
              'location', 'time_in', 'time_out', 'flow_rate_before', 'flow_rate_after']

PCM_DATA_ENTRY_UPDATE_FIELDS = ['id', 'client_sample', 'row_number', 'lab_sample', 'iwa_owa',
              'location', 'time_in', 'time_out', 'flow_rate_before', 'flow_rate_after']

class PcmMainProjectSerializer(serializers.ModelSerializer):
    pcm_project_id = serializers.IntegerField(source='pcm_project.id', read_only=True)

    class Meta:
        model = MainProject
        fields = '__all__'

class PcmDataEntryGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PcmSample
        fields = ['id', 'pcm_project', 'client_sample', 'row_number', 'lab_sample', 'iwa_owa',
                  'location', 'time_in', 'time_out', 'flow_rate_before', 'flow_rate_after',
                  'sample_volume']

class PcmSampleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PcmSample
        fields = PCM_DATA_ENTRY_CREATE_FIELDS

class PcmSampleUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)
    class Meta:
        model = PcmSample
        fields = PCM_DATA_ENTRY_UPDATE_FIELDS
        extra_kwargs = {
            f: {"required": False} for f in PCM_DATA_ENTRY_UPDATE_FIELDS
        }

class PcmDataEntryUpdateSerializer(serializers.Serializer):
    created = PcmSampleCreateSerializer(many=True, required=False)
    updated = PcmSampleUpdateSerializer(many=True, required=False)
    deleted = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        max_length=500,
    )

    def validate(self, attrs):
        print(f'attrs.get("updated", []) : {attrs.get("updated", [])}')
        updated_ids = [item["id"] for item in attrs.get("updated", [])]
        deleted_ids = attrs.get("deleted", [])

        if len(updated_ids) != len(set(updated_ids)):
            raise serializers.ValidationError(
                {"updated": ["Duplicate ids"]}
            )

        if len(deleted_ids) != len(set(deleted_ids)):
            raise serializers.ValidationError(
                {"deleted": ["Duplicate ids"]}
            )

        all_ids = set(updated_ids) | set(deleted_ids)  # taking all ids from updating and deleting
        existing = set(
            PcmSample.objects.filter(pk__in=all_ids, pcm_project__id=self.context.get("id"))
            .values_list("pk", flat=True)
        )
        missing = all_ids - existing
        if missing:
            raise serializers.ValidationError(
                {"non_field_errors": [f"Do not found: {sorted(missing)}"]}
            )

        return attrs

