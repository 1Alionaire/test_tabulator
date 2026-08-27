PLM_UPDATE_ENTRY_FIELDS = {'number_samples', 'company', 'project_name',
                           'project_address', 'sample_type_id'}   # без lab_id


@require_POST
def api_update_main_projects_table(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError as e:
        return JsonResponse({'error': f'Битый JSON: {e}'}, status=400)

    if not isinstance(payload, dict) or not isinstance(payload.get('changes'), list):
        return JsonResponse({'error': 'Ожидался {"changes": [...]}'}, status=400)

    incoming = {}
    for item in payload['changes']:
        if not isinstance(item, dict):
            continue
        lab_id = str(item.get('lab_id') or '').strip()
        fields = item.get('fields')
        if not lab_id or not isinstance(fields, dict):
            continue
        allowed = {k: v for k, v in fields.items() if k in PLM_UPDATE_ENTRY_FIELDS}
        if allowed:
            incoming[lab_id] = allowed

    if not incoming:
        return JsonResponse({'status': 'ok', 'saved': 0, 'rows': []})

    errors, to_update, touched = {}, [], set()

    with transaction.atomic():
        found = {p.lab_id: p for p in
                 MainProject.objects.select_for_update()
                                    .filter(pk__in=incoming)
                                    .order_by('lab_id_sort')}

        for lab_id, fields in incoming.items():
            project = found.get(lab_id)
            if project is None:
                errors[lab_id] = {'__all__': ['Запись не найдена']}
                continue

            form_class = modelform_factory(MainProject, form=MainProjectForm,
                                           fields=list(fields))
            form = form_class(fields, instance=project)
            if not form.is_valid():
                errors[lab_id] = form.errors
                continue

            form.save(commit=False)          # переносит cleaned_data в instance
            to_update.append(project)
            touched.update(fields)

        if errors:
            transaction.set_rollback(True)
            return JsonResponse({'errors': errors}, status=422)

        MainProject.objects.bulk_update(to_update, list(touched), batch_size=200)

    return JsonResponse({
        'status': 'ok',
        'saved': len(to_update),
        'rows': [_serialize(p) for p in to_update],
    })