from rest_framework import serializers
from tem.models import QCTEMGridRecord,TEMGridRecord

# Serializer for all PLM projects table
class QCTEMGridBookSerializer(serializers.ModelSerializer):
    plm_tem_project__project__lab_id = serializers.CharField(
        source="plm_tem_project.project.lab_id",
        read_only=True, default=None,
    )
    plm_tem_sample__lab_sample = serializers.CharField(
        source="plm_tem_sample.lab_sample",
        read_only=True, default=None,
    )
    class Meta:
        model = QCTEMGridRecord
        fields = (
            'id', 'year', 'grid_box', 'grid_id_1',
            'grid_id_2',
            'plm_tem_project__project__lab_id',
            'plm_tem_sample__lab_sample',
        )

class TEMGridBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = TEMGridRecord
        fields = (
            'id', 'year', 'position',
            'grid_box', 'grid_id_1', 'grid_id_2',
            'plm_tem_project', 'plm_tem_sample',
        )
