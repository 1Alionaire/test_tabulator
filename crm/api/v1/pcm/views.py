from main.models import MainProject, MainTypeAnalysis, MainProjectStatus, MainTurnAroundTime
from rest_framework import generics
from api.v1.pcm.serializers import PcmMainProjectSerializer
from django_filters.rest_framework import DjangoFilterBackend
from api.v1.main.views import MainProjectCursorPagination, MainProjectFilter
from django.db.models import F

class PcmMainProjectAPIList(generics.ListCreateAPIView):
    serializer_class = PcmMainProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MainProjectFilter
    pagination_class = MainProjectCursorPagination

    def get_queryset(self):
        return MainProject.active_objects.filter(project_type=MainTypeAnalysis.PCM).select_related(
            'company'
        ).annotate(pcm_project_id=F('pcm_project__id'))
