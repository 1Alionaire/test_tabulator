from .models import MainProject, MainProjectStatus
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone

def update_main_project_overdue_status():
    all_projects = MainProject.active_objects.exclude(Q(status=MainProjectStatus.Done) | Q(is_overdue=True))
    projects_to_update = []
    for project in all_projects:
        dt_register = timezone.make_aware(datetime.combine(project.date_registered, project.time_registered)) #timezone.make_aware
        elapsed = timezone.now() - dt_register
        if elapsed > timedelta(hours=project.turn_around_time):
            projects_to_update.append(project)
            setattr(project, 'is_overdue', True)
            setattr(project, 'time_update', timezone.now())

    MainProject.objects.bulk_update(projects_to_update, {'is_overdue', 'time_update'})




