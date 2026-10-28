from main.models import MainProject, MainTypeAnalysis, MainProjectStatus, MainTurnAroundTime
from rest_framework import generics
from rest_framework.pagination import CursorPagination
from .serializers import MainProjectSerializer
from django_filters.rest_framework import DjangoFilterBackend
import django_filters as df
from finance.models import Company

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

class MainProjectAPIList(generics.ListCreateAPIView):
    # queryset = MainProject.active_objects.all().filter(date_registered__year=datetime.now().year)
    serializer_class = MainProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MainProjectFilter
    pagination_class = MainProjectCursorPagination

    def get_queryset(self):
        return MainProject.active_objects.select_related(
            'company'
        )
