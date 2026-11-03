from django.db import transaction
import json
from main.models import MainProject
from django.core.management.base import BaseCommand
from finance.models import Company

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open("../../../result.txt", "r") as file:
            data = json.load(file)
        for value in data.values():
            Company.objects.create(name=value)