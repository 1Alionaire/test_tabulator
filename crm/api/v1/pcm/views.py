from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.v1.pcm.serializers import (PcmMainProjectSerializer,
                                    PcmDataEntryGetSerializer,
                                    PcmDataEntryUpdateSerializer,
                                    PcmSampleUpdateSerializer,
                                    PcmSampleCreateSerializer)
from django.db.models import F

from main.models import MainProject, MainTypeAnalysis
from pcm.models import SampleWorkArea, PcmSample, PcmProject
from api.v1.main.views import MainProjectAPIList
from rest_framework.views import APIView
from api.v1.pcm.services import PCMSamplesDataEntryManager


def get_active_pcm_project(id):
    return get_object_or_404(PcmProject.objects.select_related('project', 'analyst'),
                             pk=id, project__deleted=False)

class PcmDataEntrySampleError(Exception):
    pass

# =============== getting all options ===============
@require_GET
def get_data_entry_options(request):
    return JsonResponse({
        'sampleWorkArea': [{'value': v, 'label': l} for v, l in SampleWorkArea.choices if v is not None],
    })

class PcmMainProjectAPIList(MainProjectAPIList):
    serializer_class = PcmMainProjectSerializer
    def get_queryset(self):
        return MainProject.active_objects.filter(project_type=MainTypeAnalysis.PCM,
                                                 pcm_project__isnull=False).select_related(
                                                'company'
                                                ).annotate(pcm_project_id=F('pcm_project__id'))

class PcmSampleDataEntryList(APIView):
    def get(self, request, id):
        samples_data = PcmSample.objects.filter(pcm_project=get_active_pcm_project(id))
        serializer = PcmDataEntryGetSerializer(samples_data, many=True)
        return Response(serializer.data)

    def patch(self, request, id):
        serializer = PcmDataEntryUpdateSerializer(data=request.data, context={'id': id})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            pcm_project = get_active_pcm_project(id)
            result = PCMSamplesDataEntryManager(pcm_project = pcm_project, input_data=data, mode='update').table_update_processing()
        except PcmDataEntrySampleError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)

    def put(self, request, id):
        serializer = PcmSampleCreateSerializer(data=request.data, many=True, required=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            pcm_project = get_active_pcm_project(id)
            result = PCMSamplesDataEntryManager(pcm_project = pcm_project, input_data=data, mode='put').table_update_processing()
        except PcmDataEntrySampleError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)

