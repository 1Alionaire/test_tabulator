from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from qc.models import PcmZCriterionPerAnalystMonth
from api.v1.qc.serializers import UserPCMStdDeviationSerializer

class UserPCMStdDeviation(generics.ListCreateAPIView):
    queryset = PcmZCriterionPerAnalystMonth.objects.all()
    # serializer_class = UserPCMStdDeviationSerializer
    # permission_classes = [IsAuthenticated]
    # lookup_url_kwarg = "id"

    serializer_class = UserPCMStdDeviationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(analyst=self.request.user)