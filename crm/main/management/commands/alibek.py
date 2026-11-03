from django.core.management.base import BaseCommand
from main.models import MainTypeAnalysis


class Command(BaseCommand):
    def handle(self, *args, **options):
        print( {str(label).lower() : value for value, label in MainTypeAnalysis.choices})

