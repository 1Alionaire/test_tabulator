from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from main.models import MainProject, MainTypeAnalysis, MainTurnAroundTime, MainProjectStatus
from finance.models import Company
from pcm.models import PcmProject, PcmSample, SampleWorkArea, TypeSamplingPCM
from pcm.pcm_table_logic import calculate_sample_results
from decimal import Decimal
import calendar
import datetime
import random
import string

SAMPLES_RANGE = (5, 20)             # amount of air samples in one project
FLOW_RATE_RANGE = (2.0, 10.0)       # pump flow rate, L/min
SAMPLING_MINUTES_RANGE = (30, 240)  # time between time_in and time_out


def generate_random_string(length):
    # Choose from letters and digits
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def taken_lab_ids(date_prefix):
    # plain manager: soft-deleted projects still hold their unique lab_id
    return set(MainProject.objects.filter(lab_id__startswith=f'{date_prefix}-').values_list('lab_id', flat=True))


def next_free_lab_id(date_prefix, taken):
    # lab_id already exists -> try the next number until a free one is found
    number = 1
    while f'{date_prefix}-{number}' in taken:
        number += 1
    lab_id = f'{date_prefix}-{number}'
    taken.add(lab_id)
    return lab_id


class Command(BaseCommand):
    help = "Create test PCM projects with sampling data filled in; fiber counts are left empty"

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100, help='amount of projects to create per day')
        parser.add_argument('--year_start', type=int, default=2025, help='start year range')
        parser.add_argument('--year_end', type=int, default=2026, help='end year range')

    def handle(self, *args, **options):
        companies = list(Company.objects.all())
        if not companies:
            raise CommandError('No companies in database: create at least one Company first')

        created = 0
        for year in range(options['year_start'], options['year_end'] + 1):
            for month in range(1, 13):
                for day in range(1, calendar.monthrange(year, month)[1] + 1):
                    project_date = datetime.date(year, month, day)
                    date_prefix = project_date.strftime('%y%m%d')
                    taken = taken_lab_ids(date_prefix)  # one query per day instead of one per candidate
                    for _ in range(options['count']):
                        lab_id = next_free_lab_id(date_prefix, taken)
                        with transaction.atomic():
                            pcm_count = self.create_project(lab_id, project_date, companies)
                        created += 1
                        self.stdout.write(f'{lab_id}: {pcm_count} samples')

        self.stdout.write(self.style.SUCCESS(f'Created {created} PCM projects'))

    def create_project(self, lab_id, project_date, companies):
        pcm_count = random.randint(*SAMPLES_RANGE)

        main_project = MainProject.objects.create(lab_id=lab_id,
                                                  date_registered=project_date,
                                                  time_registered=datetime.time(10, 0),
                                                  company=random.choice(companies),
                                                  project_name=f"Project name {lab_id}",
                                                  project_address=f"Project address {lab_id}",
                                                  project_type=MainTypeAnalysis.PCM,
                                                  number_samples=pcm_count,
                                                  turn_around_time=MainTurnAroundTime.Hour24,
                                                  technician='Alibek',
                                                  status=MainProjectStatus.New,
                                                  deleted=False)

        pcm_project = PcmProject.objects.create(project=main_project,
                                                date_collect=project_date,
                                                date_analyze=project_date,
                                                date_review=project_date,
                                                work_area=f"Work area {lab_id}",
                                                technician='Alibek',
                                                type_sampling=random.choice(list(TypeSamplingPCM)))

        PcmSample.objects.bulk_create([self.generate_sample(pcm_project, lab_id, row_number, project_date)
                                       for row_number in range(1, pcm_count + 1)])
        return pcm_count

    def generate_sample(self, pcm_project, lab_id, row_number, project_date):
        flow_rate_before = Decimal(str(round(random.uniform(*FLOW_RATE_RANGE), 2)))
        # pump drifts a little during sampling
        flow_rate_after = (flow_rate_before * Decimal(str(random.uniform(0.95, 1.05)))).quantize(Decimal('0.01'))
        time_in = datetime.datetime.combine(project_date, datetime.time(random.randint(7, 11), random.choice((0, 15, 30, 45))))
        time_out = time_in + datetime.timedelta(minutes=random.randint(*SAMPLING_MINUTES_RANGE))

        sample = PcmSample(pcm_project=pcm_project,
                           row_number=row_number,
                           client_sample=str(row_number),
                           lab_sample=f'{lab_id}-{row_number}',
                           iwa_owa=random.choice((SampleWorkArea.IWA, SampleWorkArea.OWA)),
                           location=generate_random_string(12),
                           time_in=time_in.time(),
                           time_out=time_out.time(),
                           flow_rate_before=flow_rate_before,
                           flow_rate_after=flow_rate_after,
                           # fiber counts are left empty for the analysis page
                           amount_fibers=None,
                           qc_amount_fibers=None)
        calculate_sample_results(sample)  # sample_volume from time in/out and flow rates, same as the PCM page
        return sample
