from django.core.management.base import BaseCommand
from main.models import MainProject, MainProjectStatus
from finance.models import Company
import datetime
import random
import string
import math

def generate_random_string(length):
    # Choose from letters and digits
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        year = '26' # тут можно 
        companies = Company.objects.all() #
        turn_around_times = [1, 3, 6, 24]
        type_analysis = [1, 2, 3, 4]
        amount_works_every_day = 4
        help = "Create test projects with related PLM data" 

        for month_count in range(1, 13): #month
            if month_count < 10:
                month = '0' + str(month_count)
            else:
                month = str(month_count)
            for day_count in range(1, 28): # Day
                if day_count < 10:
                    day = '0' + str(day_count)
                else:
                    day = str(day_count)
                for work_count in range(1, amount_works_every_day):
                    print(f'month_count: {month_count}, work_count: {work_count}, day_count: {day_count}')
                    project_date = datetime.date(2000 + int(year), month_count, day_count)
                    MainProject.objects.create(lab_id=f'{year}{month}{day}-{str(work_count)}',
                                                            date_registered = project_date, 
                                                            time_registered = datetime.time(10, 0),
                                                            company = random.choice(companies),
                                                            project_name = generate_random_string(10), 
                                                            project_address = generate_random_string(15),
                                                            project_type = random.choice(type_analysis),
                                                            number_samples = random.randint(15, 100), 
                                                            turn_around_time = random.choice(turn_around_times),
                                                            nob_number_samples = random.randint(15, 100),
                                                            technician = 'Alibek', 
                                                            status = MainProjectStatus.New,
                                                            deleted=False)            

