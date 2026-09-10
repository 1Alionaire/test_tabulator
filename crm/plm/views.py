from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from main.models import MainProject
from django.views.generic import UpdateView
from .models import PlmProject, PlmSample
from .forms import UpdatePlmProject
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .forms import ExcelUploadForm
from openpyxl import load_workbook
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import transaction
import json
from plm.plm_table_logic import PLMSamplesDataEntryManager
# from .main_table_logic import MainProjectTableManager
# =========== utility functions =============
def return_int_value_sample_method(input_str):
    methods = {label:value for value, label in PlmSample.SampleMethod.choices}
    return methods[input_str]

# ============== render PLM main page ============
class PLMTableView(TemplateView):
    extra_context = {
        'title': 'PLM Main'
        }
    template_name = 'plm/plm_main.html'

# ============== getting all PLM projects ============
def api_get_plm_projects_table(request):
    plm_projects = MainProject.active_objects.filter(sample_type_id__in=[2,3,4]).order_by('lab_id_sort').values(
                                                     'id',
                                                     'lab_id',
                                                     'lab_id_sort',
                                                     'date_registered',
                                                     'time_registered',
                                                     'company_id',
                                                     'project_name',
                                                     'project_address',
                                                     'sample_type_id',
                                                     'number_samples',
                                                     'turn_around_time_id',
                                                     'nob_number_samples', 
                                                     'technician', 
                                                     'status_id', 
                                                     'comment')
    return JsonResponse(list(plm_projects), safe=False)

# =================== upload Excel-file for data-entry ==================
@csrf_exempt
@require_POST
def data_entry_upload_excel(request, id):
    excel_file = request.FILES.get("uploaded_file")   # "file" — имя поля из FormData

    samples_info_from_excel = []
    try:
        project_lab_id = MainProject.objects.get(plm_project__id=id).lab_id
        plm_project = PlmProject.objects.get(id=id)
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

# ============== render PLM project page  ============
class UpdateProjectView(UpdateView):
    model = PlmProject
    form_class = UpdatePlmProject
    template_name = 'plm/plm_page.html'
    context = {'title': 'test'}
    context_object_name = 'work'
    
    def get_object(self):
        return get_object_or_404(PlmProject, id=self.kwargs['id'])

# ============== getting all options ============
def api_get_table_options(request):
    return JsonResponse({
        'sampleMethod': [{'value': v, 'label': l} for v, l in PlmSample.SampleMethod.choices],
        'sampleAsbestosType' : [{'value': v, 'label': l} for v, l in PlmSample.SampleASbestosType.choices],
        'sampleTexture' : [{'value': v, 'label': l} for v, l in PlmSample.SampleTexture.choices],
        'sampleMorphology' : [{'value': v, 'label': l} for v, l in PlmSample.SampleMorphology.choices],
        'sampleSignElong' : [{'value': v, 'label': l} for v, l in PlmSample.SampleSignElong.choices],
        'sampleExtincAngle' : [{'value': v, 'label': l} for v, l in PlmSample.SampleExtincAngle.choices],
        'samplePleochColor' : [{'value': v, 'label': l} for v, l in PlmSample.SamplePleochColor.choices],
        'sampleBirefringence' : [{'value': v, 'label': l} for v, l in PlmSample.SampleBirefringence.choices],
        'sampleOtherFiber' : [{'value': v, 'label': l} for v, l in PlmSample.SampleOtherFiber.choices],
        'sampleOtherFiberProperty' : [{'value': v, 'label': l} for v, l in PlmSample.SampleOtherFiberProperty.choices],
    })

# ============== getting all data for data entry ============
def api_get_data_entry_table(request, id):
    all_samples = PlmSample.objects.filter(plm_project=id).values('id', 'homo_area', 'client_sample', 'lab_sample',
                                                                  'description', 'location', 'method', 'row_number')
    return JsonResponse(list(all_samples), safe=False)

# ============== render PLM project ============
def api_update_data_entry_table(request, id):
    plm_project = PlmProject.objects.get(pk=id)
    print(f'plm_project : {plm_project}')
    try:
        payload_json = json.loads(request.body)
        data_entry_manager = PLMSamplesDataEntryManager(input_data=payload_json, plm_project=plm_project)

        checking_error_code = data_entry_manager.validate_whole_object()

        # validating whole object
        if checking_error_code is not None:
            return JsonResponse({'status' : '!ok' , **checking_error_code}, status=400)

        print(payload_json)

        operation_result = data_entry_manager.table_update_processing()
        if operation_result['status'] == '!ok':
            return JsonResponse(**operation_result, status=400)
        
        return JsonResponse(operation_result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)