from rest_framework import serializers
from finance.models import Company

COMPANY_CREATE_FIELDS = ['name', 'slug', 'representative', 'pcm_price',
                        'plm_price', 'nob_price', 'tem_price', 'air_tem_price',
                        'lead_wipe_price', 'lead_air_price', 'vermi_price', 'mold_price']

COMPANY_UPDATE_FIELDS = [*COMPANY_CREATE_FIELDS, 'id']

# Serializer for getting all PCM samples in Data Entry Table
class CompanyGetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('__all__')

# Serializer for creating one Company in Table
class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = COMPANY_CREATE_FIELDS

# Serializer for updating one Company in Table
class CompanyUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=1)
    class Meta:
        model = Company
        fields = COMPANY_UPDATE_FIELDS
        extra_kwargs = {
            f: {"required": False} for f in COMPANY_UPDATE_FIELDS
        }

class CompanyManagerSerializer(serializers.Serializer):
    created = CompanyCreateSerializer(many=True, required=False)
    updated = CompanyUpdateSerializer(many=True, required=False)
    deleted = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        max_length=500,
    )