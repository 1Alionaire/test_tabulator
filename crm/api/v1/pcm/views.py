from datetime import datetime
import django
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status, generics

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from main.models import MainProject, MainTypeAnalysis, MainProjectStatus
from pcm.models import SampleWorkArea, PcmSample, PcmProject, SampleQCAcceptOrReject
from qc.models import PcmZCriterionPerAnalystMonth

from api.v1.pcm.services import PCMSamplesDataEntryManager, PCMSamplesAnalysisManager
from api.v1.signals import MainProjectUpdateSignal
from api.v1.main.views import MainProjectAPIList

# serializers
from api.v1.pcm.serializers import (PcmMainProjectSerializer,
                                    PcmDataEntryGetListSerializer,
                                    PcmDataEntryManagerSerializer,
                                    PcmSampleDataEntryCreateSerializer,
                                    PcmAnalystSerializer,
                                    PcmAnalysisGetListSerializer,
                                    PcmQCGetListSerializer,
                                    PcmProjectFormSerializer)
from api.v1.utils import get_active_project


class PcmDataEntrySampleError(Exception):
    pass

# =============== getting all options ===============
@require_GET
def get_data_entry_options(request):
    return JsonResponse({
        'sampleWorkArea': [{'value': v, 'label': l} for v, l in SampleWorkArea.choices if v is not None],
        'SampleQCAcceptOrReject' : [{'value': v, 'label': l} for v, l in SampleQCAcceptOrReject.choices if v is not None],
    })

class PcmMainProjectAPIList(MainProjectAPIList):
    serializer_class = PcmMainProjectSerializer
    def get_queryset(self):
        return MainProject.active_objects.filter(project_type=MainTypeAnalysis.PCM,
                                                 pcm_project__isnull=False).select_related(
                                                'company'
                                                ).annotate(pcm_project_id=F('pcm_project__id'))
# Analyst API
class PcmAnalystAPI(generics.RetrieveUpdateAPIView):
    queryset = PcmProject.objects.all()
    serializer_class = PcmAnalystSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"

    def perform_update(self, serializer):
        pcm_project = get_active_project(self.kwargs['id'], "pcm")
        pcm_analyst = self.request.user
        now_time = django.utils.timezone.now()
        z_record = PcmZCriterionPerAnalystMonth.objects.filter(month=datetime.now().month,
                                     year=datetime.now().year,
                                     analyst=pcm_analyst).first()
        MainProjectUpdateSignal(pcm_project).update_status(MainProjectStatus.InProcess)
        serializer.save(analyst=pcm_analyst,
                        date_analyze=now_time,
                        z_criterion_record=z_record,
                        time_update=now_time,
                        )

# PCM Data Entry table API
class PcmSampleDataEntry(APIView):
    def get(self, request, id):
        samples_data = PcmSample.objects.filter(pcm_project=get_active_project(id, "pcm"))
        serializer = PcmDataEntryGetListSerializer(samples_data, many=True)
        return Response(serializer.data)

    def patch(self, request, id):
        serializer = PcmDataEntryManagerSerializer(data=request.data, context={'id': id})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            pcm_project = get_active_project(id, "pcm")
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
        serializer = PcmSampleDataEntryCreateSerializer(data=request.data, many=True, required=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            pcm_project = get_active_project(id, "pcm")
            result = PCMSamplesDataEntryManager(pcm_project = pcm_project, input_data=data, mode='put').table_update_processing()
        except PcmDataEntrySampleError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)

class PcmSampleAnalysis(APIView):
    def get(self, request, id):
        samples_data = PcmSample.objects.filter(pcm_project=get_active_project(id, "pcm"))
        serializer = PcmAnalysisGetListSerializer(samples_data, many=True)
        return Response(serializer.data)

    def patch(self, request, id):
        serializer = PcmAnalysisGetListSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        print(data)
        try:
            pcm_project = get_active_project(id, "pcm")
            result = PCMSamplesAnalysisManager(pcm_project = pcm_project, input_data=data).table_update_processing()
        except PcmDataEntrySampleError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(result, status=status.HTTP_200_OK)

class PcmSampleQc(APIView):
    def get(self, request, id):
        samples_data = PcmSample.objects.filter(pcm_project=get_active_project(id, "pcm"))
        serializer = PcmQCGetListSerializer(samples_data, many=True)
        return Response(serializer.data)

    def patch(self, request, id):
        serializer = PcmQCGetListSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            pcm_project = get_active_project(id, "pcm")
            result = PCMSamplesAnalysisManager(pcm_project = pcm_project, input_data=data).table_update_processing()
        except PcmDataEntrySampleError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(result, status=status.HTTP_200_OK)

class PcmProjectInfoAPI(generics.RetrieveUpdateAPIView):
    serializer_class = PcmProjectFormSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"
    queryset = PcmProject.objects.all()