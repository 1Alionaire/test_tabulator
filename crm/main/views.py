from django.shortcuts import render
from .models import MainProject, TypeAnalysis, TurnAroundTime, ProjectStatus
from django.http import JsonResponse, FileResponse
from finance.models import Company
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.db import transaction
import django.utils

REQUIRED_ON_CREATE = {
    'company_id', 'project_name', 'project_address', 'date_registered', 'time_registered',
    'sample_type_id', 'number_samples', 'turn_around_time_id'
}

def _serialize(obj):
    return {
        'lab_id': obj.lab_id,
    }

def change_secondary_fields(input_dict):
    if 'company' in input_dict:
        input_dict['company_id'] = input_dict.pop('company') 
    if 'sample_type' in input_dict:
        input_dict['sample_type_id'] = input_dict.pop('sample_type')
    if 'turn_around_time' in input_dict:
        input_dict['turn_around_time_id'] = input_dict.pop('turn_around_time')


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
    main_projects = MainProject.objects.all().order_by('lab_id_sort').values(
                                                     'lab_id',
                                                     'lab_id_sort',
                                                     'date_registered',
                                                     'time_registered',
                                                     'company',
                                                     'project_name',
                                                     'project_address',
                                                     'sample_type',
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
        rows = json.loads(request.body).get('changes', []) # Parse rows data 
        ids = [r['lab_id'] for r in rows if r.get('lab_id')] #creating dict from data for validation
        if not ids:
            return JsonResponse({'status': 'ok'})
        
        # Checking for lab_id in every record
        for row in rows: 
            print(f'row : {row}')
            if not row.get('lab_id'): # in case lab_id is empty
                return JsonResponse({'error': 'lab_id is required'}, status=400)
 
        #creating dict, where key=lab_id and other values = value
        samples_dict_by_id = {row['lab_id']:row['fields'] for row in rows}
        print(f'samples_dict_by_id :{samples_dict_by_id}')

        with transaction.atomic():
            # parsing all existing records from our database
            existing = {
                p.pk: p for p in
                MainProject.objects.select_for_update().filter(pk__in=samples_dict_by_id)
            }

            print(existing)
            projects_to_update, projects_to_create = [], [] #init two list
            touched_fields = set()

            for lab_id, data in samples_dict_by_id.items():
                fields = {key: value for key, value in data.items() if key != 'lab_id'} # filtering data 
                # change fields that have constraints
                change_secondary_fields(fields)
                # if base already has record with lab_id
                if lab_id in existing: 
                    project = existing[lab_id] # taking project from dict
                    for field_django, field_value in fields.items(): # run through dict 
                        meta_field = MainProject._meta.get_field(field_django) # checking for secondary 
                        if meta_field.many_to_one: 
                            setattr(project, meta_field.attname, field_value )
                        else:
                            setattr(project, field_django, field_value) # put value
                        touched_fields.add(field_django) # adding to unique set of unique fields
                    project.time_update = django.utils.timezone.now() # adding time update
                    projects_to_update.append(project) # append to list projects to update

                #if base has'nt record with that lab_id
                else:
                    # checking for required fields
                    missing = REQUIRED_ON_CREATE - set(fields)
                    if missing:
                        return JsonResponse({
                            'error': 'missing required fields',
                            'lab_id': lab_id,
                            'fields': sorted(missing),
                        }, status=400)
                    # if we good then we append to list projects to create
                    projects_to_create.append(MainProject(lab_id=lab_id, status_id = 1, **fields))

            # Validation all fields
            for project in projects_to_update:
                project.full_clean(exclude=[
                    f.name for f in MainProject._meta.fields
                    if f.attname not in touched_fields
                ])

            for project in projects_to_create:
                project.full_clean()

            #final update all existing projects
            if projects_to_update:
                MainProject.objects.bulk_update(
                    projects_to_update, sorted(touched_fields | {'time_update'})
                )

            # final create all new projects
            if projects_to_create:
                for project in projects_to_create:
                    project.save()

        return JsonResponse({
                'status': 'ok',
                'rows': [_serialize(p) for p in projects_to_update],
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

