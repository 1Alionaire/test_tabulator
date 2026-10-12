from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
import json
import logging
from main.models import MainProject, MainTypeAnalysis, MainTurnAroundTime, MainProjectStatus
from .forms import UpdatePcmProject
from .models import PcmProject, PcmSample, SampleWorkArea, PcmSampleTimeTableRecord
from .pcm_table_logic import PCMSamplesDataEntryManager, PCMSamplesAnalysisManager, PCMTimeTableManager
from report_generator.pcm.pcm_report_generator import PcmReportGenerator
from utils.utils import form_errors_to_text
from qc.models import PcmZCriterionPerAnalystMonth
import django.utils
from datetime import datetime

logger = logging.getLogger(__name__)


# =============== utility functions ===============
def get_active_pcm_project(id):
    return get_object_or_404(PcmProject.objects.select_related('project', 'analyst'),
                             pk=id, project__deleted=False)


def process_table_update(request, manager_class, pcm_project, log_message):
    try:
        # parse_float=Decimal: 0.1 stays 0.1, a float would fail DecimalField validation
        payload_json = json.loads(request.body, parse_float=Decimal)
        table_manager = manager_class(pcm_project=pcm_project, input_data=payload_json)
        error = table_manager.validate_whole_object()

        # validating whole object
        if error is not None:
            return JsonResponse({'status' : '!ok' , **error}, status=400)

        return JsonResponse(table_manager.table_update_processing())

    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': '; '.join(e.messages)}, status=400)
    except IntegrityError as e:
        return JsonResponse({'error': f'database constraint failed: {e}'}, status=400)
    except Exception:
        logger.exception(log_message)
        return JsonResponse({'error': 'internal server error'}, status=500)

# =============== render PCM main page ===============
class PCMTableView(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'PCM Main'
        }
    template_name = 'pcm/pcm_main.html'


# =============== getting all PCM projects ===============
@require_GET
def api_get_pcm_projects_table(request):
    pcm_projects = MainProject.active_objects.filter(project_type=MainTypeAnalysis.PCM, pcm_project__isnull=False).order_by('-lab_id_sort').values(
                                                     'id',
                                                     'lab_id',
                                                     'lab_id_sort',
                                                     'date_registered',
                                                     'time_registered',
                                                     'company_id',
                                                     'project_name',
                                                     'project_address',
                                                     'number_samples',
                                                     'turn_around_time',
                                                     'technician',
                                                     'status',
                                                     'comment',
                                                     'pcm_project__id')
    return JsonResponse(list(pcm_projects), safe=False)

# =============== render PCM project page ===============
class UpdateProjectView(LoginRequiredMixin, UpdateView):
    model = PcmProject
    form_class = UpdatePcmProject
    template_name = 'pcm/pcm_page.html'
    context_object_name = 'work'

    def get_object(self):
        return get_active_pcm_project(self.kwargs['id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object}'
        return context

# =============== getting all options ===============
@require_GET
def api_get_table_options(request):
    return JsonResponse({
        'sampleWorkArea': [{'value': v, 'label': l} for v, l in SampleWorkArea.choices if v is not None],
    })

# =============== updating project info ===============
@require_POST
def api_update_project_info(request, id):
    form = UpdatePcmProject(request.POST, instance=get_active_pcm_project(id))
    if not form.is_valid():
        return JsonResponse({'status': '!ok', 'error': form_errors_to_text(form)}, status=400)
    form.save()
    return JsonResponse({'status': 'ok'})

# =============== analyst ===============
@require_GET
def api_get_projects_analyst(request, id):
    pcm_project = get_active_pcm_project(id)
    analyst = pcm_project.analyst.username if pcm_project.analyst else None
    return JsonResponse({'analyst': analyst})

@require_POST
def api_update_projects_analyst(request, id):
    pcm_project = get_active_pcm_project(id)
    pcm_project.analyst = request.user
    pcm_project.date_analyze = django.utils.timezone.now()
    z_record = get_object_or_404(PcmZCriterionPerAnalystMonth, month=datetime.now().month,
                                                                year=datetime.now().year,
                                                                analyst=request.user)
    pcm_project.z_criterion_record = z_record
    pcm_project.save(update_fields=['analyst', 'time_update', 'date_analyze', 'z_criterion_record'])

    return JsonResponse({'status': 'ok', 
                         'analyst': request.user.username, 
                         'low':z_record.relative_std_deviation_low,
                         'medium':z_record.relative_std_deviation_medium,
                         'high':z_record.relative_std_deviation_high})

# =============== data entry ===============
@require_GET
def api_get_data_entry_table(request, id):
    all_samples = PcmSample.objects.filter(pcm_project=get_active_pcm_project(id)).order_by('row_number').values(
                                                    'id', 'row_number', 'lab_sample', 'client_sample',
                                                    'iwa_owa', 'location', 'time_in', 'time_out',
                                                    'flow_rate_before', 'flow_rate_after', 'sample_volume')
    return JsonResponse(list(all_samples), safe=False)

@require_POST
def api_update_data_entry_table(request, id):
    return process_table_update(request, PCMSamplesDataEntryManager, get_active_pcm_project(id),
                                'pcm data entry table update failed')

# =============== analysis ===============
@require_GET
def api_get_analysis_table(request, id):
    all_samples = PcmSample.objects.filter(pcm_project=get_active_pcm_project(id)).order_by('row_number').values(
                                                    'id', 'row_number', 'lab_sample', 'client_sample', 'sample_volume',
                                                    'amount_fibers', 'fields', 'fiber_per_mm', 'fiber_per_cub_cm',
                                                    'qc_amount_fibers', 'qc_fields', 'qc_fiber_per_mm', 'qc_fiber_per_cub_cm')
    return JsonResponse(list(all_samples), safe=False)

@require_POST
def api_update_analysis_table(request, id):
    return process_table_update(request, PCMSamplesAnalysisManager, get_active_pcm_project(id),
                                'pcm analysis table update failed')

# =============== PDF report ===============
@require_GET
def generate_pcm_report(request, id):
    pcm_project = get_active_pcm_project(id)
    pdf_buffer = PcmReportGenerator(pcm_project).build()
    return FileResponse(pdf_buffer, as_attachment=True,
                        filename=f'PCM_report_{pcm_project.lab_id}.pdf',
                        content_type='application/pdf')


class PCMTimeTableByYearView(TemplateView):
    template_name = 'pcm/pcm_time_table_by_year.html'

    def get_context_data(self, **kwargs):
        #
        print(self.request.user)
        context = super().get_context_data(**kwargs)
        context['years'] = PcmSampleTimeTableRecord.objects.filter(analyst=self.request.user).values_list('year', flat=True).distinct()
                
        return context

class PCMTimeTableByMonthView(TemplateView):
    template_name = 'pcm/pcm_time_table_by_month.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.kwargs.get('year'))
        context['year'] = year
        context['months'] = (
                PcmSampleTimeTableRecord.objects.filter(analyst=self.request.user, year=year)
                    .values_list('month', flat=True).distinct()
            )
        return context

class PCMTimeTableByDayView(TemplateView):
    template_name = 'pcm/pcm_time_table_by_select_day.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.kwargs.get('year'))
        month = int(self.kwargs.get('month'))
        day = int(self.kwargs.get('day'))
        context['year'] = year
        context['month'] = month
        context['selected_day'] = day
        context['days'] = (
                        PcmSampleTimeTableRecord.objects.filter(analyst=self.request.user, year=year, month=month)
                            .values_list('day', flat=True).distinct()
                    )
        return context

# =============== getting all PCM projects ===============
@require_GET
def api_get_time_table(request, year, month, day):
    time_table = PcmSampleTimeTableRecord.objects.filter(analyst=request.user, year=year, month=month, day=day).order_by('row_number').values(
                                                     'id',
                                                     'row_number',
                                                     'year',
                                                     'month',
                                                     'day',
                                                     'project',
                                                     'start_time',
                                                     'end_time')
    return JsonResponse(list(time_table), safe=False)

@require_POST
def api_update_time_table(request, year, month, day):
    try:
        # parse_float=Decimal: 0.1 stays 0.1, a float would fail DecimalField validation
        payload_json = json.loads(request.body, parse_float=Decimal)
        print(payload_json)
        return JsonResponse(PCMTimeTableManager(input_data=payload_json,
                                   year=year,
                                   month=month,
                                   day = day,
                                   user=request.user).table_update_processing()) 
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': '; '.join(e.messages)}, status=400)
    except IntegrityError as e:
        return JsonResponse({'error': f'database constraint failed: {e}'}, status=400)
    except Exception:
        logger.exception('pcm time table update failed')
        return JsonResponse({'error': 'internal server error'}, status=500)
