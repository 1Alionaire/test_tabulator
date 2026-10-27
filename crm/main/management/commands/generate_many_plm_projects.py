from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from main.models import MainProject, MainTypeAnalysis, MainTurnAroundTime, MainProjectStatus
from finance.models import Company
from plm.models import PlmProject, PlmSample, PlmSampleWeight, SampleMethod
from utils.utils import generate_weight_item
import datetime
import random
import string

SAMPLES_RANGE = (10, 30)  # amount of samples of every type (198.1 and 198.6) in one project


def generate_random_string(length):
    # Choose from letters and digits
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def next_free_lab_id(date_prefix):
    number = 1
    while MainProject.objects.filter(lab_id=f'{date_prefix}-{number}').exists():
        number += 1
    return f'{date_prefix}-{number}'


class Command(BaseCommand):
    help = "Create test PLM projects with 198.1 and 198.6 samples; every 198.6 sample gets a weight record"

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='amount of projects to create')

    def handle(self, *args, **options):
        companies = list(Company.objects.all())
        # today = timezone.localdate()

        for year in ('2020', '2021', '2022', '2023', '2024', '2025', '2026'):
            for month in range(1, 13):
                for day in range(1, 28):
                    for work in range(1, 400):
                        with transaction.atomic():
                            current_date = datetime.datetime.strptime(f'{year}-{month}-{day}', "%Y-%m-%d")
                            main_project, plm_count, nob_count = self.create_project(current_date, companies)
                        self.stdout.write(f'{main_project.lab_id}: {plm_count} x 198.1, {nob_count} x 198.6')

    # dateparser.parse('1991-05-17')
    # datetime.datetime(1991, 5, 17, 0, 0)

    def create_project(self, project_date, companies):
        plm_count = random.randint(*SAMPLES_RANGE)
        nob_count = random.randint(*SAMPLES_RANGE)

        lab_id = next_free_lab_id(project_date.strftime('%y%m%d'))
        main_project = MainProject.objects.create(lab_id=lab_id,
                                                  date_registered=project_date,
                                                  time_registered=datetime.time(10, 0),
                                                  company=random.choice(companies),
                                                  project_name=f"Project name {lab_id}",
                                                  project_address= f"Project address {lab_id}",
                                                  project_type=MainTypeAnalysis.TEM,
                                                  number_samples=plm_count,
                                                  turn_around_time=MainTurnAroundTime.Hour24,
                                                  nob_number_samples=nob_count,
                                                  technician='Alibek',
                                                  status=MainProjectStatus.New,
                                                  deleted=False)

        plm_project = PlmProject.objects.create(project=main_project, date_collect=project_date)

        methods = [SampleMethod.Sample1981] * plm_count + [SampleMethod.Sample1986] * nob_count
        homo_area = 1
        samples_left_in_area = random.randint(1, 3)
        for row_number, method in enumerate(methods, start=1):
            client_sample = str(row_number)

            weight = None
            if method == SampleMethod.Sample1986:
                weight = PlmSampleWeight.objects.create(plm_project=plm_project,
                                                        client_sample=client_sample,
                                                        **generate_weight_item())

            PlmSample.objects.create(plm_project=plm_project,
                                     homo_area=str(homo_area),
                                     row_number=row_number,
                                     layer=1,
                                     client_sample=client_sample,
                                     lab_sample=f'{main_project.lab_id}-{row_number}',
                                     description=generate_random_string(12),
                                     location=generate_random_string(12),
                                     method=method,
                                     weight=weight,
                                     # asbestos results are left empty (points keep 50 = "not counted")
                                     asb_type=None,
                                     asb_percent=None,
                                     tem_asb_type=None,
                                     tem_asb_percent=None)

            samples_left_in_area -= 1
            if samples_left_in_area == 0:
                homo_area += 1
                samples_left_in_area = random.randint(1, 3)

        return main_project, plm_count, nob_count
