from django.http import JsonResponse
from django.views.decorators.http import require_GET

from main.models import MainProject, MainTypeAnalysis, MainProjectStatus, MainTurnAroundTime
from rest_framework import generics
from api.v1.pcm.serializers import PcmMainProjectSerializer
from django_filters.rest_framework import DjangoFilterBackend
from api.v1.main.views import MainProjectCursorPagination, MainProjectFilter
from django.db.models import F

from pcm.models import SampleWorkArea


class PcmMainProjectAPIList(generics.ListCreateAPIView):
    serializer_class = PcmMainProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MainProjectFilter
    pagination_class = MainProjectCursorPagination

    def get_queryset(self):
        return MainProject.active_objects.filter(project_type=MainTypeAnalysis.PCM,
                                                 pcm_project__isnull=False).select_related(
                                                'company'
                                                ).annotate(pcm_project_id=F('pcm_project__id'))

# =============== getting all options ===============
@require_GET
def get_data_entry_options(request):
    return JsonResponse({
        'sampleWorkArea': [{'value': v, 'label': l} for v, l in SampleWorkArea.choices if v is not None],
    })