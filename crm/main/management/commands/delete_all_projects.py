from main.models import MainProject
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        MainProject.objects.all().delete()