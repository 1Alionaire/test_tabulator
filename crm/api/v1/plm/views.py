from datetime import datetime
import django
from django.db.models import F, Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.v1.main.views import MainProjectAPIList

from api.v1.plm.serializers import (PlmMainProjectSerializer, # Main project in main page
                                    PlmAnalystSerializer,
                                    PlmSampleEntryGetListSerializer,
                                    PlmSampleEntryCreateSerializer,
                                    PlmEntryManagerSerializer,
                                    PlmWeightGetListSerializer,
                                    PlmWeightManagerSerializer,
                                    PlmNobAnalysisTableSerializer,
                                    PlmTemAnalysisTableSerializer,
                                    PlmTemperatureSerializer,
                                    PlmProjectFormSerializer)

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
                        SampleOtherFiberProperty,
                        PlmSample,
                        PlmSampleWeight)

from api.v1.signals import MainProjectUpdateSignal
from api.v1.utils import get_active_project

from api.v1.plm.services import (PLMSamplesEntryManager,
                                 PLMSamplesWeightManager,
                                 update_plm_nob_tem_analysis)
from django.utils import timezone

class PlmEntrySampleError(Exception):
    pass

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
        project = get_active_project(self.kwargs['id'], "plm")
        analyst = self.request.user
        MainProjectUpdateSignal(project).update_status(MainProjectStatus.InProcess)
        serializer.save(analyst=analyst,
                        date_analyze=timezone.now())

class PlmSampleDataEntry(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        samples_data = PlmSample.objects.filter(plm_project=get_active_project(id, 'plm')).exclude(Q(is_qc_sample=True) |
                                                                                                   Q(tem_is_qc_sample=True) |
                                                                                                   Q(is_blank=True))
        serializer = PlmSampleEntryGetListSerializer(samples_data, many=True)
        return Response(serializer.data)

    def patch(self, request, id):
        serializer = PlmEntryManagerSerializer(data=request.data, context={'id': id})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = get_active_project(id, "plm")
            result = PLMSamplesEntryManager(plm_project=project,
                                            input_data=data,
                                            mode='patch').table_update_processing()
        except VersionConflictError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PlmEntrySampleError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"error": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)

    def put(self, request, id):
        serializer = PlmSampleEntryCreateSerializer(data=request.data, many=True, required=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = get_active_project(id, "plm")
            result = PLMSamplesEntryManager(plm_project=project,
                                            input_data=data,
                                            mode='put').table_update_processing()
        except PlmEntrySampleError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)

class PlmSampleWeightAPI(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        samples_data = PlmSampleWeight.objects.filter(plm_project=get_active_project(id, 'plm'))
        serializer = PlmWeightGetListSerializer(samples_data, many=True)
        return Response(serializer.data)

    def patch(self, request, id):
        serializer = PlmWeightManagerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = get_active_project(id, "plm")
            result = PLMSamplesWeightManager(plm_project=project,
                                            input_data=data).table_update_processing()
        except VersionConflictError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PlmEntrySampleError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)

class PlmNobAnalysisApi(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PlmNobAnalysisTableSerializer
    pagination_class = None  # если в settings задана пагинация по умолчанию, а таблица нужна целиком

    def get_queryset(self):
        return (
            PlmSample.objects
            .filter(plm_project_id=self.kwargs["id"])  # подставь своё имя FK на проект
            .select_related("weight")
            .order_by("row_number")
        )

    def patch(self, request, id):
        serializer = PlmNobAnalysisTableSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = get_active_project(id, "plm")
            result = update_plm_nob_tem_analysis(data, project)
        except PlmEntrySampleError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except VersionConflictError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)

class PlmTemAnalysisApi(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PlmTemAnalysisTableSerializer
    pagination_class = None  # если в settings задана пагинация по умолчанию, а таблица нужна целиком

    def get_queryset(self):
        return (
            PlmSample.objects
            .filter(plm_project_id=self.kwargs["id"])  # подставь своё имя FK на проект
            .select_related("weight")
            .order_by("row_number")
        )

    def patch(self, request, id):
        serializer = PlmTemAnalysisTableSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = get_active_project(id, "plm")
            result = update_plm_nob_tem_analysis(data, project)
        except PlmEntrySampleError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except VersionConflictError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)

class PlmTemperature(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PlmTemperatureSerializer
    lookup_url_kwarg = "id"
    def get_object(self):
        sample = (
            PlmSample.objects
            .filter(plm_project_id=self.kwargs["id"])
            .order_by("row_number", "pk")
            .first()
        )
        if sample is None:
            raise Http404("В проекте нет сэмплов.")
        self.check_object_permissions(self.request, sample)
        return sample

class PlmProjectInfoAPI(generics.RetrieveUpdateAPIView):
    serializer_class = PlmProjectFormSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"
    queryset = PlmProject.objects.all()
