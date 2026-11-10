
import django
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status, generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from finance.models import Company
from api.v1.finance.serializers import (CompanyGetListSerializer,
                                        CompanyManagerSerializer)

from api.v1.finance.services import CompanyPriceTableManager

class CompanyPriceError(Exception):
    pass

class CompanyPriceTableView(generics.GenericAPIView):
    def get(self, request):
        samples_data = Company.objects.all().order_by('name')
        serializer = CompanyGetListSerializer(samples_data, many=True)
        return Response(serializer.data)

    def patch(self, request):
        serializer = CompanyManagerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            result = CompanyPriceTableManager(input_data=data).table_update_processing()
        except CompanyPriceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InterruptedError:
            return Response(
                {"detail": "Data integrity constraint violation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)