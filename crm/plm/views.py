from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse, FileResponse, Http404
from django.views.generic import UpdateView
from .forms import UpdatePlmProject, PlmProjectDateCollect
from django.shortcuts import  redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from openpyxl import load_workbook
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from plm.plm_table_logic import (generate_qc_entry_process,
                                 validate_plm_project,
                                 complete_qc_process,)
import django.utils
from tem.models import TEMGridRecord
from report_generator.plm.plm_report_generator import BulkSampleReportGenerator
from invoice_generator.invoice_generator import InvoiceGenerator, DataForInvoiceGenerator
import logging
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from utils.utils import form_errors_to_text
from api.v1.signals import MainProjectUpdateSignal
from main.models import MainProject, MainTypeAnalysis, MainProjectStatus

logger = logging.getLogger(__name__)
from .models import (
    PlmProject,
    PlmSample,
    SampleMethod,
)

# =============== utility functions ===============
def return_int_value_sample_method(input_str):
    methods = {label:value for value, label in SampleMethod.choices}
    return methods[input_str]


def get_active_plm_project(id):
    return get_object_or_404(PlmProject.objects.select_related('project', 'analyst'),
                             pk=id, project__deleted=False)

# =============== render PLM main page ===============
class PLMTableView(LoginRequiredMixin, TemplateView):
    extra_context = {
        'title': 'PLM Main'
        }
    template_name = 'plm/plm_main.html'

# =============== upload Excel-file for data-entry ===============
@csrf_exempt
@require_POST
def data_entry_upload_excel(request, id):
    excel_file = request.FILES.get("uploaded_file")   # "file" — имя поля из FormData

    samples_info_from_excel = []
    try:
        project_lab_id = MainProject.objects.get(plm_project__id=id).lab_id
        plm_project = get_active_plm_project(id)
        wb = load_workbook(excel_file, data_only=True)
        ws_entry = wb['PLM-Entry']

        excel_row = 4
        while True: 
            value = ws_entry[f'F{excel_row}'].value
            if value is None or not str(value).strip():
                break
            samples_info_from_excel.append(PlmSample(plm_project = plm_project,
                                                     row_number = excel_row - 3,
                                                    homo_area = str(ws_entry[f'A{excel_row}'].value),
                                                    client_sample = str(ws_entry[f'B{excel_row}'].value),
                                                    description = str(ws_entry[f'C{excel_row}'].value),
                                                    location = str(ws_entry[f'D{excel_row}'].value),
                                                    method = return_int_value_sample_method(str(ws_entry[f'E{excel_row}'].value)),
                                                    lab_sample = (project_lab_id + '-' + str(excel_row - 3))) )
            excel_row += 1

        with transaction.atomic():
            if PlmSample.objects.filter(plm_project__id=id).exists():
                PlmSample.objects.filter(plm_project__id=id).delete()
            for project in samples_info_from_excel:
                project.full_clean()
                project.save()

        return redirect('plm:plm_detail', id=id)  
            
    except Exception as e:
        print(e)
    return redirect('plm:plm_detail', id=id)  

# =============== render PLM project page  ===============
class UpdateProjectView(LoginRequiredMixin, UpdateView):
    model = PlmProject
    form_class = UpdatePlmProject
    template_name = 'plm/plm_page.html'
    context_object_name = 'work'
    
    def get_object(self):
        return get_active_plm_project(self.kwargs['id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object}'
        context.setdefault("date_collect_form", PlmProjectDateCollect(instance=self.object))
        return context

@require_POST
def api_update_projects_date_collect(request, id):
    form = PlmProjectDateCollect(request.POST, instance=get_active_plm_project(id))
    if not form.is_valid():
        return JsonResponse({'status': '!ok', 'error': form_errors_to_text(form)}, status=400)
    form.save()
    return JsonResponse({'status': 'ok'})

@require_POST
def api_update_project_info(request, id):
    form = UpdatePlmProject(request.POST, instance=get_active_plm_project(id))
    if not form.is_valid():
        return JsonResponse({'status': '!ok', 'error': form_errors_to_text(form)}, status=400)
    form.save()
    return JsonResponse({'status': 'ok'})

@require_POST
def api_generate_qc_samples(request, id):
    try:
        with transaction.atomic():
            created_samples = generate_qc_entry_process(id)
            return JsonResponse({'status': 'ok', 'created':created_samples})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': '; '.join(e.messages)}, status=400)
    except IntegrityError as e:
        return JsonResponse({'error': f'database constraint failed: {e}'}, status=400)
    except Exception:
        logger.exception('update project analyst error')
        return JsonResponse({'error': 'internal server error'}, status=500)

def api_complete_qc_process(request, id):
    plm_project = get_object_or_404(PlmProject, pk=id)
    errors = validate_plm_project(plm_project, for_what='qc')
    if errors:
        return JsonResponse({'status' : '!ok' , 'error': errors}, status=400)
    try:
        with transaction.atomic():  
            made_qc_items = complete_qc_process(plm_project)
            PlmProject.objects.filter(pk=id).update(qc_completed=True)
            return JsonResponse({'status': 'ok', 'generated':made_qc_items})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    except ValidationError as e:
        return JsonResponse({'error': '; '.join(e.messages)}, status=400)
    except IntegrityError as e:
        return JsonResponse({'error': f'database constraint failed: {e}'}, status=400)
    except Exception:
        logger.exception('update project analyst error')
        return JsonResponse({'error': 'internal server error'}, status=500)


# =============== PDF report ===============
@require_GET
def generate_plm_report(request, id):
    plm_project = get_object_or_404(PlmProject.objects.select_related('project__company'), pk=id)
    #validate whole project
    errors = validate_plm_project(plm_project, for_what='report')
    if errors:
        return JsonResponse({'status' : '!ok' , 'error': errors}, status=400)
    pdf_buffer = BulkSampleReportGenerator(plm_project).build()
    MainProjectUpdateSignal(plm_project).update_status(MainProjectStatus.Done)
    return FileResponse(pdf_buffer, as_attachment=True,
                        filename=f'PLM_report_{plm_project.lab_id}.pdf',
                        content_type='application/pdf')

def generate_invoice(request, id):
    main_project = MainProject.active_objects.filter(plm_project__id=id)
    plm_project = get_object_or_404(PlmProject, id=id)
    #validate whole project
    errors = validate_plm_project(plm_project, for_what='report')
    if errors:
        return JsonResponse({'status' : '!ok' , 'error': errors}, status=400)
    if not main_project.exists():  # удалённый или несуществующий проект
        raise Http404('Project not found')
    pdf_buffer = InvoiceGenerator(main_project).build()
    return FileResponse(pdf_buffer, as_attachment=True,
                            filename=f'Invoice.pdf',
                            content_type='application/pdf')

