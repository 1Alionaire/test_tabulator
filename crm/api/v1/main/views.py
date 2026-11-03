# from "vanilla" django
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db import IntegrityError
# from models
from main.models import MainProject, MainTypeAnalysis, MainProjectStatus, MainTurnAroundTime
from finance.models import Company
# from rest_framework
from rest_framework import generics
from rest_framework.pagination import CursorPagination
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
# from service files
from .services import MainProjectError, MainProjectTableManager
from .serializers import MainProjectSerializer, MainProjectChangesSerializer
# from django-filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters as df
import logging

logger = logging.getLogger(__name__)
@require_GET
def get_main_project_table_options(request):
    return JsonResponse({
        'status': [{'value': v, 'label': l} for v, l in MainProjectStatus.choices],
        'project_type': [{'value': v, 'label': l} for v, l in MainTypeAnalysis.choices],
        'turn_around_time': [{'value': v, 'label': l} for v, l in MainTurnAroundTime.choices],
        'company': [
            {'value': o.pk, 'label': o.name}
            for o in Company.objects.order_by('name')
        ],
        'years':[]
    })

class MainProjectFilter(df.FilterSet):
    # имя атрибута = имя query-параметра
    date_registered__gte = df.DateFilter(field_name='date_registered', lookup_expr='gte')
    date_registered__lte = df.DateFilter(field_name='date_registered', lookup_expr='lte')

    # ModelMultipleChoiceFilter читает getlist() — повторяющиеся ключи работают из коробки
    project_type      = df.TypedMultipleChoiceFilter(choices=MainTypeAnalysis.choices, coerce=int)
    status            = df.TypedMultipleChoiceFilter(choices=MainProjectStatus.choices, coerce=int)
    turn_around_time  = df.TypedMultipleChoiceFilter(choices=MainTurnAroundTime.choices, coerce=int)
    company = df.ModelMultipleChoiceFilter(queryset=Company.objects.all())

    lab_id           = df.CharFilter(lookup_expr='icontains')
    project_name     = df.CharFilter(lookup_expr='icontains')
    project_address  = df.CharFilter(lookup_expr='icontains')

    class Meta:
        model = MainProject
        fields = ['company']

class MainProjectCursorPagination(CursorPagination):
    # курсор строится по первому полю; id — тай-брейкер для стабильного порядка
    ordering = ('-lab_id_sort', '-id')
    page_size = 200
    page_size_query_param = 'page_size'
    max_page_size = 500

class MainProjectAPIList(generics.ListAPIView):
    serializer_class = MainProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MainProjectFilter
    pagination_class = MainProjectCursorPagination

    def get_queryset(self):
        return MainProject.active_objects.select_related(
            'company'
        )

class MainProjectChangesView(APIView):
    def post(self, request):
        serializer = MainProjectChangesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = MainProjectTableManager(data, request.user).table_update_processing()
        except MainProjectError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except IntegrityError:
            logger.exception("IntegrityError в projects-update")
            return Response(
                {"detail": "Нарушено ограничение целостности данных."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result,status=status.HTTP_200_OK)