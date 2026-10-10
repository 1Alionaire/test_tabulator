from django.shortcuts import render
from .models import MainProject, MainTypeAnalysis, MainTurnAroundTime, MainProjectStatus
from django.http import JsonResponse, FileResponse
from finance.models import Company
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.db import transaction
import django.utils
from .main_table_logic import MainProjectTableManager
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from .forms import ProjectCOCUpload
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from plm.models import PlmProject
from pcm.models import PcmProject
from django.views.decorators.http import require_GET, require_POST
import logging
from django.core.exceptions import ValidationError
from django.db import IntegrityError

logger = logging.getLogger(__name__)

def _serialize(obj):
    return {
        'lab_id': obj.lab_id,
    }

class MainTableView(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'Main'
        }
    template_name = 'main/index.html'

@require_GET
def api_get_table_options(request):
    return JsonResponse({
        'status': [{'value': v, 'label': l} for v, l in MainProjectStatus.choices],
        'project_type': [{'value': v, 'label': l} for v, l in MainTypeAnalysis.choices],
        'turn_around_time': [{'value': v, 'label': l} for v, l in MainTurnAroundTime.choices],
        'company': [
            {'value': o.pk, 'label': o.name}
            for o in Company.objects.order_by('name')
        ],
    })

@require_GET
def api_get_main_projects_table(request):
    main_projects = MainProject.active_objects.all().order_by('-lab_id_sort').values(
                                                     'id',
                                                     'lab_id',
                                                     'lab_id_sort',
                                                     'date_registered',
                                                     'time_registered',
                                                     'company_id',
                                                     'project_name',
                                                     'project_address',
                                                     'project_type',
                                                     'number_samples',
                                                     'turn_around_time',
                                                     'nob_number_samples', 
                                                     'technician', 
                                                     'status', 
                                                     'comment')
    return JsonResponse(list(main_projects), safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def api_update_main_projects_table(request):
    try:
        payload_json = json.loads(request.body)
        table_manager = MainProjectTableManager(payload_json)
        error = table_manager.validate_whole_object()

        # validating whole object
        if error is not None:
            return JsonResponse({'status' : '!ok' , **error}, status=400)

        # updating 
        return JsonResponse(table_manager.table_update_processing())
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': '; '.join(e.messages)}, status=400)
    except IntegrityError as e:
        return JsonResponse({'error': f'database constraint failed: {e}'}, status=400)
    except Exception:
        logger.exception('main table update failed')
        return JsonResponse({'error': 'internal server error'}, status=500)


class UploadCOCView(UpdateView):
    model = MainProject
    form_class = ProjectCOCUpload
    template_name = 'main/coc_upload_page.html'
    context = {'title': 'Upload COC'}
    context_object_name = 'work'
    
    def get_object(self):
        return get_object_or_404(MainProject, id=self.kwargs['id'])

    def get_success_url(self):
        return reverse_lazy('main:main')

def route_work(request, id):
    main_project = MainProject.objects.get(pk=id)
    if main_project.project_type == MainTypeAnalysis.PCM:
        pcm_project = get_object_or_404(PcmProject, project=main_project)
        return redirect('pcm:pcm_detail', pcm_project.id)
    if main_project.project_type in [MainTypeAnalysis.Bulk, MainTypeAnalysis.BulkTEM, MainTypeAnalysis.TEM]:
        plm_project = get_object_or_404(PlmProject, project=main_project) 
        return redirect('plm:plm_detail', plm_project.id)