from main.models import MainProject, MainTypeAnalysis, MainProjectStatus, MainTurnAroundTime
from rest_framework import generics
from .serializers import MainProjectSerializer
from datetime import datetime
from django_filters.rest_framework import DjangoFilterBackend
import django_filters as df
from finance.models import Company

ALLOWED_LIST = ALLOWED = {'lab_id', 'date_registered', 'project_type', 'company',
                    'status', 'turn_around_time', 'project_name', 'project_address'}

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

class MainProjectAPIList(generics.ListCreateAPIView):
    # queryset = MainProject.active_objects.all().filter(date_registered__year=datetime.now().year)
    serializer_class = MainProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MainProjectFilter

    def get_queryset(self):
        return MainProject.active_objects.select_related(
            'company'
        )
