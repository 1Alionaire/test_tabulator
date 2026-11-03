from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.v1.pcm.serializers import PcmMainProjectSerializer, PcmDataEntrySerializer
from django.db.models import F

from main.models import MainProject, MainTypeAnalysis
from pcm.models import SampleWorkArea, PcmSample, PcmProject
from api.v1.main.views import MainProjectAPIList
from rest_framework.views import APIView

def get_active_pcm_project(id):
    return get_object_or_404(PcmProject.objects.select_related('project', 'analyst'),
                             pk=id, project__deleted=False)

# =============== getting all options ===============
@require_GET
def get_data_entry_options(request):
    return JsonResponse({
        'sampleWorkArea': [{'value': v, 'label': l} for v, l in SampleWorkArea.choices if v is not None],
    })

class PcmMainProjectAPIList(MainProjectAPIList):
    serializer_class = PcmMainProjectSerializer
    def get_queryset(self):
        return MainProject.active_objects.filter(project_type=MainTypeAnalysis.PCM,
                                                 pcm_project__isnull=False).select_related(
                                                'company'
                                                ).annotate(pcm_project_id=F('pcm_project__id'))

class PcmSampleDataEntryList(APIView):
    def get(self, request, id):
        samples_data = PcmSample.objects.filter(pcm_project=get_active_pcm_project(id))
        serializer = PcmDataEntrySerializer(samples_data, many=True)
        return Response(serializer.data)

