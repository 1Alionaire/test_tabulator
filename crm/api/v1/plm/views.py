from datetime import datetime
import django
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status, generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from api.v1.main.views import MainProjectAPIList

from api.v1.plm.serializers import (PlmMainProjectSerializer,
                                    PlmAnalystSerializer)

from main.models import MainProject, MainTypeAnalysis, MainProjectStatus
from plm.models import (PlmProject,
                        SampleMethod,
                        SampleASbestosType,
                        SampleTexture,
                        SampleMorphology,
                        SampleSignElong,
                        SampleExtincAngle,
                        SamplePleochColor,
                        SampleBirefringence,
                        SampleOtherFiber,
                        SampleOtherFiberProperty)

from api.v1.signals import MainProjectUpdateSignal


def get_active_plm_project(id):
    return get_object_or_404(PlmProject.objects.select_related('project', 'analyst'),
                             pk=id, project__deleted=False)

class PlmMainProjectAPIList(MainProjectAPIList):
    serializer_class = PlmMainProjectSerializer
    def get_queryset(self):
        return MainProject.active_objects.filter(project_type__in=[MainTypeAnalysis.Bulk,
                                                                   MainTypeAnalysis.BulkTEM,
                                                                   MainTypeAnalysis.EPT],
                                                 plm_project__isnull=False).select_related(
                                                'company'
                                                ).annotate(plm_project_id=F('plm_project__id'))


# =============== getting all options ===============
@require_GET
def get_table_options(request):
    return JsonResponse({
        'sampleMethod': [{'value': v, 'label': l} for v, l in SampleMethod.choices],
        'sampleAsbestosType' : [{'value': v, 'label': l} for v, l in SampleASbestosType.choices],
        'sampleTexture' : [{'value': v, 'label': l} for v, l in SampleTexture.choices],
        'sampleMorphology' : [{'value': v, 'label': l} for v, l in SampleMorphology.choices],
        'sampleSignElong' : [{'value': v, 'label': l} for v, l in SampleSignElong.choices],
        'sampleExtincAngle' : [{'value': v, 'label': l} for v, l in SampleExtincAngle.choices],
        'samplePleochColor' : [{'value': v, 'label': l} for v, l in SamplePleochColor.choices],
        'sampleBirefringence' : [{'value': v, 'label': l} for v, l in SampleBirefringence.choices],
        'sampleOtherFiber' : [{'value': v, 'label': l} for v, l in SampleOtherFiber.choices],
        'sampleOtherFiberProperty': [{'value': v, 'label': l} for v, l in SampleOtherFiberProperty.choices],
    })

# Analyst API
class PlmAnalystAPI(generics.RetrieveUpdateAPIView):
    queryset = PlmProject.objects.all()
    serializer_class = PlmAnalystSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"
    def perform_update(self, serializer):
        project = get_active_plm_project(self.kwargs['id'])
        analyst = self.request.user
        now_time = django.utils.timezone.now()

        MainProjectUpdateSignal(project).update_status(MainProjectStatus.InProcess)
        serializer.save(analyst=analyst,
                        date_analyze=now_time,
                        time_update=now_time,
                        )
