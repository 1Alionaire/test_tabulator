from rest_framework import serializers
from main.models import MainProject
from plm.models import PlmProject, PlmSample

PLM_DATA_ENTRY_CREATE_FIELDS = ['row_number', 'client_sample', 'homo_area', 'layer',
                  'description', 'location', 'method', 'lab_sample' ]

PLM_DATA_ENTRY_UPDATE_FIELDS = [*PLM_DATA_ENTRY_CREATE_FIELDS, 'id']

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

# Serializer for getting all PCM samples in Data Entry Table
class PlmDataEntryGetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlmSample
        fields = PLM_DATA_ENTRY_UPDATE_FIELDS

# Serializer for creating one PLM sample in Data Entry Table
class PlmSampleEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlmSample
        fields = PLM_DATA_ENTRY_CREATE_FIELDS

# Serializer for updating one PCM sample in Data Entry Table
class PlmSampleEntryUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)
    class Meta:
        model = PlmSample
        fields = PLM_DATA_ENTRY_UPDATE_FIELDS
        extra_kwargs = {
            f: {"required": False} for f in PLM_DATA_ENTRY_UPDATE_FIELDS
        }

# Nested Serializer for batch updating PCM samples in Data Entry Table
class PlmEntryManagerSerializer(serializers.Serializer):
    created = PlmSampleEntryCreateSerializer(many=True, required=False)
    updated = PlmSampleEntryUpdateSerializer(many=True, required=False)
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
            PlmSample.objects.filter(pk__in=all_ids, plm_project__id=self.context.get("id"))
            .values_list("pk", flat=True)
        )
        missing = all_ids - existing
        if missing:
            raise serializers.ValidationError(
                {"non_field_errors": [f"Do not found: {sorted(missing)}"]}
            )

        return attrs