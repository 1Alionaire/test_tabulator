
from django.utils import timezone
from django.db import transaction

from plm.models import PlmProject, PlmSample, PlmSampleWeight

class PLMSamplesEntryManager():
    def __init__(self, plm_project, input_data, mode):
        self.plm_project = plm_project
        self.input_data = input_data
        self.now_moment = timezone.now()
        self.mode = mode
        if self.mode == 'patch':
            self.data_to_update = input_data.get('updated', [])
            self.data_to_create = input_data.get('created', [])
            self.data_to_delete = input_data.get('deleted', [])

    def table_update_processing(self) -> dict:
        if self.mode == 'patch':
            result = {}
            with transaction.atomic():
                if self.data_to_delete:
                    result['deleted'] = self._delete_data()
                if self.data_to_update:
                    result['updated'] = self._update_data()
                if self.data_to_create:
                    result['created'] = self._create_data()

        elif self.mode == 'put':
            samples = []
            with transaction.atomic():
                PlmSample.objects.filter(plm_project=self.plm_project).delete()
                for data in self.input_data:
                    data['row_number'] = int(data['row_number'])
                    samples.append(PlmSample(plm_project=self.plm_project, **data))

                for sample in samples:
                    sample.save()

            result = {'created':len(samples)}

        return result

    def _update_data(self):
        work_data = self.data_to_update
        update_ids = {int(item['id']) for item in work_data}
        touched_fields = set()

        samples_to_update = {sample.id: sample for sample in
                             PlmSample.objects.select_for_update().filter(pk__in=update_ids)}

        for element in work_data:
            print(f'element : {element}')
            sample = samples_to_update[int(element['id'])]
            for field_name, value in element.items():
                if field_name != 'id':
                    setattr(sample, field_name, value)
                    touched_fields.add(field_name)
            setattr(sample, 'time_update', self.now_moment)

        return PlmSample.objects.bulk_update(
            samples_to_update.values(), sorted(touched_fields | {'time_update'})
        )

    def _create_data(self):
        samples = []
        for data in self.data_to_create:
            samples.append(PlmSample(plm_project=self.plm_project, **data))

        for sample in samples:
            sample.save()

        return len(samples)

    def _delete_data(self):
        PlmSample.objects.filter(id__in=self.data_to_delete).delete()
        return len(self.data_to_delete)

