from finance.models import Company
from django.db import transaction
from django.utils.text import slugify
from django.utils import timezone

class CompanyPriceTableManager():
    def __init__(self, input_data):
        self.input_data = input_data
        self.data_to_update = input_data.get('updated', [])
        self.data_to_create = input_data.get('created', [])
        self.data_to_delete = input_data.get('deleted', [])
        self.now_moment = timezone.now()

    def table_update_processing(self) -> dict:
        result = {'status': 'ok'}
        with transaction.atomic():
            if self.data_to_update:
                result['updated'] = self._update_data()
            if self.data_to_create:
                result['created'] = self._create_data()
        return result

    def _update_data(self) -> int:
        work_data = self.data_to_update
        id_list = [element.get('id') for element in work_data]
        touched_fields = set()

        companies_to_update = {project.id : project for project in
                               Company.objects.select_for_update().filter(pk__in=id_list)}

        for record_row in work_data:
            company = companies_to_update[int(record_row.get('id'))]
            for name_field, value in record_row.items():
                if name_field != 'id':
                    setattr(company, name_field, value)
                    touched_fields.add(name_field)
            setattr(company, 'time_update', self.now_moment)

        return Company.objects.bulk_update(
            companies_to_update.values(), sorted(touched_fields | {'time_update'})
        )

    def _create_data(self) -> int:
        objects = []
        for data in self.data_to_create:
            objects.append(Company(**data, slug=slugify(data['name'])))
        Company.objects.bulk_create(objects)
        return len(objects)
