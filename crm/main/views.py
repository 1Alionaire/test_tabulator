from django.shortcuts import render
from .models import MainProject, TypeAnalysis, TurnAroundTime, ProjectStatus
from django.http import JsonResponse, FileResponse
from finance.models import Company
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.db import transaction

def main(request):
    return render(request, 'main/index.html')

PLM_UPDATE_ENTRY_FIELDS = ['date_registered', 
                           'time_registered','company', 'project_name', 'project_address', 
                           'sample_type_id','number_samples', 'turn_around_time', 'nob_number_samples', 
                           'technician', 'status', 'comment']

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
    main_projects = MainProject.objects.all().values(
                                                     'lab_id',
                                                     'date_registered',
                                                     'time_registered',
                                                     'company',
                                                     'project_name',
                                                     'project_address',
                                                     'sample_type_id',
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
        rows = json.loads(request.body).get('changes', [])  # parsing json
        ids = [r['lab_id'] for r in rows if r.get('lab_id')] # making dict

        if not ids:
            return JsonResponse({'status': 'ok'})
        
        samples_dict_by_id = {r['lab_id']: r for r in rows if r.get('lab_id')}


        with transaction.atomic():
            existing = {
            p.pk: p for p in
                MainProject.objects.select_for_update().filter(pk__in=ids)
            }
            to_update, to_create = [], []
            projects = list(
                MainProject.objects.select_for_update()
                              .filter(lab_id__in=ids)
            )
            all_fields = []

            for project in projects:
                row = samples_dict_by_id[project.lab_id]
                for key, value in row["fields"].items():
                    field = MainProject._meta.get_field(key)
                    if field.many_to_one:
                        setattr(project, field.attname, value )
                    else:
                        setattr(project, key, value)

                    all_fields.append(key)

            all_fields = list(set(all_fields))

            MainProject.objects.bulk_update(
                                                projects,
                                                all_fields
                                            )

        return JsonResponse({
                'status': 'ok',
                # 'rows': [_serialize(p) for p in to_update],
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

