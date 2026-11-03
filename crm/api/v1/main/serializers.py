from rest_framework import serializers
from main.models import MainProject

MAIN_PROJECT_UPDATE_FIELDS = ['id', 'lab_id_sort', 'lab_id', 'date_registered', 'time_registered',
                  'company', 'project_number', 'project_name', 'project_address', 'project_type', 'number_samples',
                  'turn_around_time', 'nob_number_samples', 'status', 'technician', 'comment',
                  'is_overdue',]

MAIN_PROJECT_CREATE_FIELDS = ['lab_id_sort', 'lab_id', 'date_registered', 'time_registered',
                  'company', 'project_number', 'project_name', 'project_address', 'project_type', 'number_samples',
                  'turn_around_time', 'nob_number_samples', 'status', 'technician', 'comment',
                  'is_overdue']


class MainProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainProject
        fields = ('__all__')

class MainProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainProject
        fields = MAIN_PROJECT_CREATE_FIELDS
        extra_kwargs = {
            f: {"required": False} for f in MAIN_PROJECT_CREATE_FIELDS
        }

class MainProjectUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)

    class Meta:
        model = MainProject
        fields = MAIN_PROJECT_UPDATE_FIELDS
        extra_kwargs = {
            f: {"required": False} for f in MAIN_PROJECT_UPDATE_FIELDS
        }
        validators = []

class MainProjectChangesSerializer(serializers.Serializer):
    created = MainProjectCreateSerializer(many=True, required=False)
    updated = MainProjectUpdateSerializer(many=True, required=False)
    deleted = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        max_length=500,
    )

    def validate(self, attrs):
        # Validate updated data
        updated_ids = [item["id"] for item in attrs.get("updated", [])]

        if len(updated_ids) != len(set(updated_ids)):
            raise serializers.ValidationError(
                {"updated": ["Duplicate ids"]}
            )

        deleted_ids = attrs.get("deleted", [])

        if len(deleted_ids) != len(set(deleted_ids)):
            raise serializers.ValidationError(
                {"deleted": ["Duplicate ids"]}
            )

        all_ids = set(updated_ids) | set(deleted_ids) # taking all ids from updating and deleting
        existing = set(
            MainProject.active_objects.filter(pk__in=all_ids)
            .values_list("pk", flat=True)
        )
        missing = all_ids - existing
        if missing:
            raise serializers.ValidationError(
                {"non_field_errors": [f"Do not found: {sorted(missing)}"]}
            )
        return attrs
