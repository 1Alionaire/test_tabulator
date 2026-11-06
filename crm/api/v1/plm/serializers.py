from rest_framework import serializers
from main.models import MainProject
from plm.models import PlmProject, PlmSample, PlmSampleWeight

PLM_DATA_ENTRY_CREATE_FIELDS = ['row_number', 'client_sample', 'homo_area', 'layer',
                  'description', 'location', 'method', 'lab_sample' ]

PLM_DATA_ENTRY_UPDATE_FIELDS = [*PLM_DATA_ENTRY_CREATE_FIELDS, 'id']

PLM_WEIGHT_CREATE_FIELDS = ['client_sample', 'w_crucible',
                           'w_crucible_with_sample', 'w_sample', 'w_sample_ashed',
                           'org',  'w_petri', 'w_petri_with_sample',
                           'residue', 'caco3']

PLM_WEIGHT_UPDATE_FIELDS = [*PLM_WEIGHT_CREATE_FIELDS, 'id']

PLM_WEIGHT_GET_LIST_FIELDS = [*PLM_WEIGHT_CREATE_FIELDS, 'id', 'sample']

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

# ============== Getting Data Entry Serializer ================
class PlmSampleEntryGetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlmSample
        fields = PLM_DATA_ENTRY_UPDATE_FIELDS

# ============== Updating Data Entry Serializer ================
# Serializer for creating one PLM sample in Data Entry Table
class PlmSampleEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlmSample
        fields = PLM_DATA_ENTRY_CREATE_FIELDS

# Serializer for updating one PLM sample in Data Entry Table
class PlmSampleEntryUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)
    class Meta:
        model = PlmSample
        fields = PLM_DATA_ENTRY_UPDATE_FIELDS
        extra_kwargs = {
            f: {"required": False} for f in PLM_DATA_ENTRY_UPDATE_FIELDS
        }

# Nested Serializer for batch updating PLM samples in Data Entry Table
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

# ================ Weight get serializer ====================
class SampleForWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlmSample
        fields = ['id', 'row_number', 'lab_sample', 'is_blank', 'is_qc_sample']
# Nested Weight serializer
class PlmWeightGetListSerializer(serializers.ModelSerializer):
    sample = SampleForWeightSerializer(read_only=True)

    class Meta:
        model = PlmSampleWeight
        fields = PLM_WEIGHT_GET_LIST_FIELDS

# ================ Weight update serializer ====================
class PlmWeightCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlmSampleWeight
        fields = PLM_WEIGHT_CREATE_FIELDS

class PlmWeightUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)
    class Meta:
        model = PlmSampleWeight
        fields = PLM_WEIGHT_UPDATE_FIELDS

# Nested Serializer for batch updating PCM samples in Data Entry Table
class PlmWeightManagerSerializer(serializers.Serializer):
    created = PlmWeightCreateSerializer(many=True, required=False)
    updated = PlmWeightUpdateSerializer(many=True, required=False)
    deleted = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        max_length=500,
    )

class PlmNobAnalysisTableSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)
    weight__residue = serializers.DecimalField(
        source="weight.residue", max_digits=10, decimal_places=4,
        read_only=True, default=None,
    )
    class Meta:
        model = PlmSample
        fields = ['id', 'row_number', 'tem_na_or_ps', 'client_sample', 'lab_sample',
                  'layer', 'color', 'texture', 'homo_area', 'morphology',
                  'ri_alpha_oil', 'ri_delta_oil', 'sign_of_elongation', 'extinction_angle', 'pleochroism_color',
                  'birefringence', 'other_fiber', 'other_fiber_property', 'other_fiber_percent', 'asb_type',
                  'asb_point_1', 'asb_point_2', 'asb_point_3', 'asb_point_4', 'asb_point_5', 'asb_point_6', 'asb_point_7', 'asb_point_8',
                  'asb_percent', 'method', 'weight__residue' ]
