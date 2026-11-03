import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import Company
from main.models import MainProject, MainProjectStatus, MainTurnAroundTime, MainTypeAnalysis
from .models import PcmProject, PcmSample


class DataEntrySaveTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('analyst', password='x')
        main_project = MainProject.objects.create(
            lab_id='26-0001', project_name='School', project_address='1 Main St',
            company=Company.objects.create(name='ACME'), project_type=MainTypeAnalysis.PCM,
            turn_around_time=MainTurnAroundTime.Hour24, status=MainProjectStatus.New, number_samples=3,
        )
        cls.pcm_project = PcmProject.objects.create(project=main_project)

    def setUp(self):
        self.client.force_login(self.user)
        self.samples = [
            PcmSample.objects.create(pcm_project=self.pcm_project, row_number=i, lab_sample=f'26-0001-{i}',
                                     client_sample=f'C-{i}', amount_fibers=Decimal('10.0'))
            for i in (1, 2, 3)
        ]

    def post(self, url_name, payload):
        return self.client.post(reverse(f'pcm:{url_name}', args=[self.pcm_project.id]),
                                data=json.dumps(payload), content_type='application/json')

    def saved_rows(self):
        return list(PcmSample.objects.filter(pcm_project=self.pcm_project).order_by('row_number')
                    .values_list('row_number', 'lab_sample', 'client_sample'))

    # ---------- update: edited saved rows + new rows at the end ----------
    def test_update_saves_edited_rows_and_keeps_analysis_results(self):
        edited = self.samples[1]
        response = self.post('api_update_data_entry_table', {
            'updated': [{'id': edited.id, 'client_sample': 'C-2 edited', 'time_in': '08:00', 'time_out': '10:00',
                         'flow_rate_before': '2.0', 'flow_rate_after': '2.0', 'sample_volume': None}],
            'created': [],
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'updated': 1, 'created': 0})
        edited.refresh_from_db()
        self.assertEqual(edited.client_sample, 'C-2 edited')
        self.assertEqual(edited.sample_volume, Decimal('240.00'))   # 2 L/min * 120 min, calculated on the server
        self.assertEqual(edited.amount_fibers, Decimal('10.0'))     # analysis result is kept
        self.assertEqual(self.saved_rows(), [(1, '26-0001-1', 'C-1'), (2, '26-0001-2', 'C-2 edited'),
                                             (3, '26-0001-3', 'C-3')])

    def test_update_appends_new_rows_after_saved_ones(self):
        response = self.post('api_update_data_entry_table', {'updated': [], 'created': [{'client_sample': 'C-4'}, {}]})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'updated': 0, 'created': 2})
        self.assertEqual(self.saved_rows()[3:], [(4, '26-0001-4', 'C-4'), (5, '26-0001-5', '')])

    def test_update_rejects_inconsistent_rows(self):
        first_id = self.samples[0].id
        payloads = {
            'updated row without id': {'updated': [{'client_sample': 'X'}], 'created': []},
            'new row with id': {'updated': [], 'created': [{'id': first_id, 'client_sample': 'X'}]},
            'duplicate ids': {'updated': [{'id': first_id}, {'id': first_id}], 'created': []},
            'not a json object': [{'id': first_id}],
        }
        for name, payload in payloads.items():
            with self.subTest(name):
                self.assertEqual(self.post('api_update_data_entry_table', payload).status_code, 400)

    def test_update_saves_nothing_when_a_sample_is_gone(self):
        response = self.post('api_update_data_entry_table', {
            'updated': [{'id': self.samples[0].id, 'client_sample': 'X'}, {'id': 999999, 'client_sample': 'Y'}],
            'created': [{'client_sample': 'NEW'}],
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.saved_rows(), [(1, '26-0001-1', 'C-1'), (2, '26-0001-2', 'C-2'),
                                             (3, '26-0001-3', 'C-3')])

    # ---------- replace all: rows deleted or inserted above saved rows ----------
    def test_replace_all_follows_table_order(self):
        # new row on top, C-2 deleted, C-1 moved below C-3
        response = self.post('api_replace_all_data_entry_table', {'rows': [
            {'client_sample': 'NEW'},
            {'id': self.samples[2].id, 'client_sample': 'C-3'},
            {'id': self.samples[0].id, 'client_sample': 'C-1'},
        ]})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'deleted': 3, 'created': 3})
        self.assertEqual(self.saved_rows(), [(1, '26-0001-1', 'NEW'), (2, '26-0001-2', 'C-3'),
                                             (3, '26-0001-3', 'C-1')])
        # like PLM: replacing all samples does not keep analysis results
        self.assertFalse(PcmSample.objects.filter(pcm_project=self.pcm_project, amount_fibers__isnull=False).exists())

    def test_replace_all_with_empty_table_deletes_every_sample(self):
        response = self.post('api_replace_all_data_entry_table', {'rows': []})

        self.assertEqual(response.json(), {'status': 'ok', 'deleted': 3, 'created': 0})
        self.assertEqual(self.saved_rows(), [])

    def test_replace_all_saves_nothing_on_invalid_row(self):
        response = self.post('api_replace_all_data_entry_table', {'rows': [
            {'client_sample': 'NEW'},
            {'time_in': 'not a time'},
        ]})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.saved_rows(), [(1, '26-0001-1', 'C-1'), (2, '26-0001-2', 'C-2'),
                                             (3, '26-0001-3', 'C-3')])
