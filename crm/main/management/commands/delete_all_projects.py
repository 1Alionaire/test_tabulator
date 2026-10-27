from django.db import transaction

from main.models import MainProject
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        projects_amount = MainProject.active_objects.all().values_list('id', flat=True)
        chunks = [projects_amount[i:i + 100] for i in range(0, len(projects_amount), 100)]
        for chunk in chunks:
            with transaction.atomic():
                MainProject.active_objects.filter(id__in=chunk).delete()