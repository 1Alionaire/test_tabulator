from django.core.management.base import BaseCommand
from pcm.models import PcmSampleTimeTableRecord
from django.conf import settings
from users.models import User
month_day_dict = {
    1:31,
    2:28,
    3:31,
    4:30,
    5:31,
    6:30,
    7:31,
    8:31,
    9:30,
    10:31,
    11:30,
    12:31
}

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        admin_user = User.objects.get(username='admin')
        years = [ 2026]

        for iter_year in years:
            for iter_month, count_day in month_day_dict.items():
                for iter_day in range(1, count_day+1):
                    PcmSampleTimeTableRecord.objects.create(analyst=admin_user,
                                                            year=iter_year,
                                                            month=iter_month,
                                                            day=iter_day)




