from django.shortcuts import render
from .models import MainProject, TypeAnalysis, TurnAroundTime, ProjectStatus
from django.http import JsonResponse, FileResponse
from finance.models import Company
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.db import transaction
import django.utils
from .main_table_logic import MainProjectTableManager

def _serialize(obj):
    return {
        'lab_id': obj.lab_id,
    }

def main(request):
    return render(request, 'main/index.html')

def api_get_table_options(request):
    return JsonResponse({
        'status': [
            {'value': o.pk, 'label': o.status_name}
            for o in ProjectStatus.objects.all()
        ],
        'sample_type': [
            {'value': o.pk, 'label': o.analysis_name}
            for o in TypeAnalysis.objects.all()
        ],
        'turn_around_time': [
            {'value': o.pk, 'label': o.label}
            for o in TurnAroundTime.objects.order_by('hour')
        ],
        'company': [
            {'value': o.pk, 'label': o.name}
            for o in Company.objects.order_by('name')
        ],
    })

def api_get_main_projects_table(request):
    main_projects = MainProject.active_objects.all().order_by('lab_id_sort').values(
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
    return JsonResponse(list(main_projects), safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def api_update_main_projects_table(request):
    try:
        payload_json = json.loads(request.body)

        table_manager = MainProjectTableManager(payload_json)
        checking_error_code = table_manager.validate_whole_object()

        # validating whole object
        if checking_error_code is not None:
            return JsonResponse({'status' : '!ok' , **checking_error_code}, status=400)

        # updating 
        operation_result = table_manager.table_update_processing()
        if operation_result['status'] == '!ok':
            return JsonResponse(**operation_result, status=400)

        return JsonResponse(operation_result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

