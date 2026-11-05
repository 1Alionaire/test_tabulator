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

from api.v1.plm.serializers import (PlmMainProjectSerializer
                                    )

from main.models import MainProject, MainTypeAnalysis, MainProjectStatus

class PlmMainProjectAPIList(MainProjectAPIList):
    serializer_class = PlmMainProjectSerializer
    def get_queryset(self):
        return MainProject.active_objects.filter(project_type__in=[MainTypeAnalysis.Bulk,
                                                                   MainTypeAnalysis.BulkTEM,
                                                                   MainTypeAnalysis.EPT],
                                                 plm_project__isnull=False).select_related(
                                                'company'
                                                ).annotate(plm_project_id=F('plm_project__id'))
# Analyst API