from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Max
from rest_framework import status, generics
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tem.models import QCTEMGridRecord, TEMGridRecord
from api.v1.tem.serializers import QCTEMGridBookSerializer, TEMGridBookSerializer
import django_filters as df
from django.db import transaction

class QCTEMGridBook(generics.ListAPIView):
    serializer_class = QCTEMGridBookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only the logged-in analyst's records, newest month first
        return (QCTEMGridRecord.objects.all().select_related('plm_tem_project', 'plm_tem_sample')
                .order_by('-pk'))

    def perform_create(self, serializer):
        serializer.save(analyst=self.request.user)

class MainProjectFilter(df.FilterSet):
    # имя атрибута = имя query-параметра
    plm_tem_project = df.CharFilter(lookup_expr='icontains')
    plm_tem_sample = df.CharFilter(lookup_expr='icontains')

class GridBoxCursorPagination(CursorPagination):
    page_size = 1000
    max_page_size = 1000
    ordering = ("-grid_box", "position")   # или ("-box_number", "number"), если номер коробки — поле в таблице

class TEMGridBook(generics.ListAPIView):
    serializer_class = TEMGridBookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MainProjectFilter
    pagination_class = GridBoxCursorPagination

    def get_queryset(self):
        return TEMGridRecord.objects.all()

class TEMGridBookChangesView(generics.GenericAPIView):
    serializer_class = TEMGridBookSerializer
    @transaction.atomic
    def post(self, request):
        last_box = TEMGridRecord.objects.aggregate(Max('grid_box'))
        current_year = 2026
        for position, grids in TEMGridRecord.all_grid_id.items():
            TEMGridRecord.objects.create(position=position,
                                         year=current_year,
                                         grid_box=last_box['grid_box__max'] + 1,
                                         grid_id_1=grids[0],
                                         grid_id_2=grids[1])
        return Response({'created':25}, status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request):
        pass

