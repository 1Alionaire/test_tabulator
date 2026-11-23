from tem.models import TEMGridRecord
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        years = [2026]
        counter = 1

        for iter_year in years:
            for iter_grid_box in range(1, 10):
                for position, grids in TEMGridRecord.all_grid_id.items():
                    TEMGridRecord.objects.create(position=position,
                                                year = iter_year, 
                                                grid_box=iter_grid_box,
                                                grid_id_1 = grids[0],
                                                grid_id_2 = grids[1])

