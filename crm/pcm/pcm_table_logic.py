from .models import PcmSampleTimeTableRecord
from django.db import transaction
from django.utils import timezone
import django.utils

class PCMTimeTableManager():
    def __init__(self, input_data, year, month, day, user):
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])
        self.year = year
        self.month = month
        self.day = day
        self.user = user

    def table_update_processing(self) -> dict:
        result = {'status': 'ok'}
        with transaction.atomic():
            if self.data_to_update:
                result['updated'] = self._update_data()
            if self.data_to_create:
                result['created'] = self._create_data()
        return result

    def _update_data(self):
        work_data = self.data_to_update
        id_list = [element.get('id') for element in work_data]

        records_for_update = {record.id : record for record in 
                                            PcmSampleTimeTableRecord.objects.select_for_update().filter(pk__in=id_list).order_by('id')}

        for record_row in work_data:
            sample = records_for_update[int(record_row.get('id'))]
            setattr(sample, 'project', record_row['project'])
            setattr(sample, 'start_time', record_row['start_time'])
            setattr(sample, 'end_time', record_row['end_time'])
            setattr(sample, 'row_number', record_row['row_number'])
            sample.time_update = django.utils.timezone.now()

        updated = PcmSampleTimeTableRecord.objects.bulk_update(
                                records_for_update.values(), sorted({'time_update', 'project', 'start_time', 'row_number', 'end_time'})
                            )

        return updated

    def _create_data(self):
        time_table_array = []
        data = self.data_to_create
        for record in data:
            time_table_array.append(PcmSampleTimeTableRecord(
                analyst = self.user,
                year = self.year,
                month = self.month,
                day = self.day,
                start_time = record['start_time'], 
                end_time = record['end_time'], 
                row_number = record['row_number'], 
                project = record['project'], 
            ))

        for record in time_table_array:
            record.full_clean()
            record.save()

        return len(time_table_array)

def validate_pcm_project_for_report(pcm_project):
    errors = []
    fields = {'analyst' : 'No analyst',
            'date_collect' : 'No date collect',
            'date_analyze':'No date analysis', 
            'work_area': 'No work area',
            'technician': 'No technician',
            'rotometer':'No rotometer',
            'type_sampling' : 'No type sampling'}

    for field, text_error in fields.items():
        if getattr(pcm_project, field) == None or getattr(pcm_project, field) == '':
            errors.append(text_error)

    return errors