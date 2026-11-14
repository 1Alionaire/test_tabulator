from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from qc.models import PcmZCriterionPerAnalystMonth
from api.v1.qc.serializers import UserPCMStdDeviationSerializer

class UserPCMStdDeviation(generics.ListCreateAPIView):
    # serializer_class = UserPCMStdDeviationSerializer
    # permission_classes = [IsAuthenticated]
    # lookup_url_kwarg = "id"

    serializer_class = UserPCMStdDeviationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only the logged-in analyst's records, newest month first
        return (PcmZCriterionPerAnalystMonth.objects
                .filter(analyst=self.request.user)
                .order_by('-year', '-month', '-id'))

    def perform_create(self, serializer):
        serializer.save(analyst=self.request.user)

class UserPCMStdDeviationDetail(generics.RetrieveUpdateAPIView):
    serializer_class = UserPCMStdDeviationSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"

    def get_queryset(self):
        # an analyst can change only own records; someone else's id -> 404
        return PcmZCriterionPerAnalystMonth.objects.filter(analyst=self.request.user)