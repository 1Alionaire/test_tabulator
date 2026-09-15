from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from main.models import MainProject
from django.views.generic import UpdateView
from .forms import UpdatePlmProject
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from openpyxl import load_workbook
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from plm.plm_table_logic import PLMSamplesDataEntryManager, PLMSamplesWeightManager
import django.utils

from .models import (
    PlmProject,
    PlmSample,
    PlmSampleWeight,
    SampleMethod,
    SampleASbestosType,
    SampleTexture,
    SampleMorphology,
    SampleSignElong,
    SampleExtincAngle,
    SamplePleochColor,
    SampleBirefringence,
    SampleOtherFiber,
    SampleOtherFiberProperty,
)


# =============== utility functions ===============
def return_int_value_sample_method(input_str):
    methods = {label:value for value, label in PlmSample.SampleMethod.choices}
    return methods[input_str]

# =============== render PLM main page ===============
class PLMTableView(TemplateView):
    extra_context = {
        'title': 'PLM Main'
        }
    template_name = 'plm/plm_main.html'

# =============== getting all PLM projects ===============
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

# =============== upload Excel-file for data-entry ===============
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

# =============== render PLM project page  ===============
class UpdateProjectView(UpdateView):
    model = PlmProject
    form_class = UpdatePlmProject
    template_name = 'plm/plm_page.html'
    context = {'title': 'test'}
    context_object_name = 'work'
    
    def get_object(self):
        return get_object_or_404(PlmProject, id=self.kwargs['id'])

# =============== getting all options ===============
def api_get_table_options(request):
    return JsonResponse({
        'sampleMethod': [{'value': v, 'label': l} for v, l in SampleMethod.choices],
        'sampleAsbestosType' : [{'value': v, 'label': l} for v, l in SampleASbestosType.choices],
        'sampleTexture' : [{'value': v, 'label': l} for v, l in SampleTexture.choices],
        'sampleMorphology' : [{'value': v, 'label': l} for v, l in SampleMorphology.choices],
        'sampleSignElong' : [{'value': v, 'label': l} for v, l in SampleSignElong.choices],
        'sampleExtincAngle' : [{'value': v, 'label': l} for v, l in SampleExtincAngle.choices],
        'samplePleochColor' : [{'value': v, 'label': l} for v, l in SamplePleochColor.choices],
        'sampleBirefringence' : [{'value': v, 'label': l} for v, l in SampleBirefringence.choices],
        'sampleOtherFiber' : [{'value': v, 'label': l} for v, l in SampleOtherFiber.choices],
        'sampleOtherFiberProperty': [{'value': v, 'label': l} for v, l in SampleOtherFiberProperty.choices],
    })

# =============== getting all data for data entry ===============
def api_get_data_entry_table(request, id):
    all_samples = PlmSample.objects.filter(plm_project=id).order_by('row_number').values('id', 'homo_area', 'client_sample', 'lab_sample',
                                                                  'description', 'layer', 'location', 'method', 'row_number', 'is_blank', 'is_qc_sample')
    return JsonResponse(list(all_samples), safe=False)

# =============== render PLM project ===============
def api_update_data_entry_table(request, id):
    plm_project = PlmProject.objects.get(pk=id)
    try:
        payload_json = json.loads(request.body)
        data_entry_manager = PLMSamplesDataEntryManager(input_data=payload_json, 
                                                        plm_project=plm_project, 
                                                        type='update')

        checking_error_code = data_entry_manager.validate_whole_object()

        # validating whole object
        if checking_error_code is not None:
            return JsonResponse({'status' : '!ok' , **checking_error_code}, status=400)

        operation_result = data_entry_manager.table_update_processing()
        if operation_result['status'] == '!ok':
            return JsonResponse(**operation_result, status=400)
        
        return JsonResponse(operation_result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def api_replace_all_data_entry_table(request, id):
    plm_project = PlmProject.objects.get(pk=id)
    try:
        payload_json = json.loads(request.body)

        data_entry_manager = PLMSamplesDataEntryManager(input_data=payload_json, 
                                                        plm_project=plm_project, 
                                                        type='replace_all')

        checking_error_code = data_entry_manager.validate_whole_object()

        if checking_error_code is not None:
            return JsonResponse({'status' : '!ok' , **checking_error_code}, status=400)

        operation_result = data_entry_manager.table_update_processing()
        if operation_result['status'] == '!ok':
            return JsonResponse(**operation_result, status=400)
        
        return JsonResponse(operation_result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# =============== getting all data for weight ===============
def api_get_weight_table(request, id):
    all_weights = PlmSampleWeight.objects.filter(plm_project=id).order_by('sample__row_number', 'client_sample').values('id', 'sample__row_number', 'sample__lab_sample', 'client_sample', 'w_crucible', 
                                                                                                       'w_crucible_with_sample', 'w_sample', 'w_sample_ashed', 
                                                                                                       'org',  'w_petri', 'w_petri_with_sample', 
                                                                                                       'residue', 'caco3', 'sample__is_blank')

    return JsonResponse(list(all_weights), safe=False)

# =============== updating weight table ===============
def api_update_weight_table(request, id):
    plm_project = PlmProject.objects.get(pk=id)
    payload_json = json.loads(request.body)
    print(f'payload_json : {payload_json}')

    weight_manager = PLMSamplesWeightManager(plm_project=plm_project,input_data=payload_json)
    checking_error_code = weight_manager.validate_whole_object()

    if checking_error_code is not None:
        return JsonResponse({'status' : '!ok' , **checking_error_code}, status=400)

    operation_result = weight_manager.table_update_processing()
    if operation_result['status'] == '!ok':
        return JsonResponse(**operation_result, status=400)
    
    return JsonResponse(operation_result)

# =============== getting all data for NOB analysis ===============
def api_get_nob_analysis_table(request, id):
    all_samples = PlmSample.objects.filter(plm_project=id).order_by('row_number').values('row_number', 'id', 'homo_area', 
                                                                                        'client_sample', 'lab_sample', 'layer', 'method', 
                                                                                        'color', 'weight__residue', 'is_qc_sample', 
                                                                                        'analysis_temperature', 'texture', 'morphology', 
                                                                                        'ri_alpha_oil', 'ri_delta_oil', 'sign_of_elongation', 
                                                                                        'extinction_angle', 'pleochroism_color', 'birefringence', 
                                                                                        'other_fiber', 'other_fiber_property', 'other_fiber_percent', 'asb_type',
                                                                                        'asb_point_1', 'asb_point_2', 'asb_point_3', 'asb_point_4',
                                                                                        'asb_point_5', 'asb_point_6', 'asb_point_7', 'asb_point_8', 
                                                                                        'asb_percent')
    return JsonResponse(list(all_samples), safe=False)

def api_update_nob_analysis_table(request, id):
    selected_plm_project = PlmProject.objects.get(pk=id)
    payload_json = json.loads(request.body)
    touched_fields = set()
    try:
        with transaction.atomic():
            samples_to_update = {sample.id : sample for sample in 
                                            PlmSample.objects.select_for_update().filter(plm_project=selected_plm_project)}
            for record_row in payload_json:
                sample = samples_to_update[int(record_row.get('id'))]
                for name_field, value in record_row.items():
                    if name_field not in ['id', 'weight__residue']:
                        setattr(sample, name_field, value)
                        touched_fields.add(name_field)
                sample.time_update = django.utils.timezone.now()

            PlmSample.objects.bulk_update(samples_to_update.values(), sorted(touched_fields | {'time_update'}))
                        
            return JsonResponse({'status':'ok'})
            

    except Exception as e:
        return JsonResponse({'status':'!ok', "error": f"{str(e)}"})

# =============== getting all data for NOB analysis ===============
def api_get_tem_analysis_table(request, id):
    all_samples = PlmSample.objects.filter(plm_project=id, method__in=[2,3,4]).order_by('row_number').values('id', 'row_number', 'client_sample', 'method', 
                                                                                        'lab_sample', 'layer', 'homo_area', 'weight__residue', 
                                                                                         'tem_asb_type', 'tem_asb_point', 'tem_asb_percent', 
                                                                                         'tem_microscope_alignment', 'tem_eccentricity_adjusted', 'tem_grid_pre_acceptability', 
                                                                                         'tem_grid_box', 'tem_grid_box_id_1', 'tem_grid_box_id_2', 'tem_na_or_ps', 'is_tem_qc_sample', 'is_blank')
    return JsonResponse(list(all_samples), safe=False)