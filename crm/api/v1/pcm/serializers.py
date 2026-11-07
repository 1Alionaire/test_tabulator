from rest_framework import serializers
from main.models import MainProject
from pcm.models import PcmProject, PcmSample

PCM_DATA_ENTRY_CREATE_FIELDS = ['client_sample', 'row_number', 'lab_sample', 'iwa_owa',
              'location', 'time_in', 'time_out', 'flow_rate_before', 'flow_rate_after']

PCM_DATA_ENTRY_UPDATE_FIELDS = [*PCM_DATA_ENTRY_CREATE_FIELDS, 'id']

PCM_DATA_ENTRY_GET_LIST_FIELDS = [*PCM_DATA_ENTRY_CREATE_FIELDS, 'id', 'sample_volume']

# Serializer for all PCM projects table
class PcmMainProjectSerializer(serializers.ModelSerializer):
    pcm_project_id = serializers.IntegerField(source='pcm_project.id', read_only=True)

    class Meta:
        model = MainProject
        fields = '__all__'

class PcmAnalystSerializer(serializers.ModelSerializer):
    analyst_username = serializers.CharField(
        source="analyst.username",
        read_only=True,
        allow_null=True,
    )
    class Meta:
        model = PcmProject
        fields = ['analyst', "analyst_username"]

# Serializer for getting all PCM samples in Data Entry Table
class PcmDataEntryGetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PcmSample
        fields = PCM_DATA_ENTRY_GET_LIST_FIELDS

# Serializer for creating one PCM sample in Data Entry Table
class PcmSampleDataEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PcmSample
        fields = PCM_DATA_ENTRY_CREATE_FIELDS

# Serializer for updating one PCM sample in Data Entry Table
class PcmSampleDataEntryUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)
    class Meta:
        model = PcmSample
        fields = PCM_DATA_ENTRY_UPDATE_FIELDS
        extra_kwargs = {
            f: {"required": False} for f in PCM_DATA_ENTRY_UPDATE_FIELDS
        }

# Nested Serializer for batch updating PCM samples in Data Entry Table
class PcmDataEntryManagerSerializer(serializers.Serializer):
    created = PcmSampleDataEntryCreateSerializer(many=True, required=False)
    updated = PcmSampleDataEntryUpdateSerializer(many=True, required=False)
    deleted = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        max_length=500,
    )

    def validate(self, attrs):
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

# Serializer for getting all PCM samples in Data Analysis Table
class PcmAnalysisGetListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)
    class Meta:
        model = PcmSample
        fields = ['id',  'lab_sample',  'client_sample', 'location', 'sample_volume',
                  'amount_fibers', 'fields', 'segment_area', 'fiber_per_mm', 'fiber_per_cub_cm',]

class PcmQCGetListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)
    class Meta:
        model = PcmSample
        fields = ['id',  'lab_sample',  'client_sample',
                  'amount_fibers', 'fields', 'fiber_per_mm', 'fiber_per_cub_cm',
                  'qc_amount_fibers', 'segment_area', 'qc_fields', 'qc_fiber_per_mm', 'qc_fiber_per_cub_cm']
