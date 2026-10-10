import re
from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from finance.models import Company
from main.models import MainProject, ProjectStatus, TurnAroundTime, TypeAnalysis
from report_generator.common import fmt_fixed, fmt_number
from report_generator.pcm.pcm_report_generator import COLUMNS, PcmReportGenerator, is_above_limit
from .models import PcmProject, PcmSample
from .pcm_table_logic import average_flow_rate, calculate_fiber_results, calculate_sample_volume, sampling_minutes

from main.models import MainTypeAnalysis

def page_count(pdf_bytes):
    return len(re.findall(rb'/Type /Page[^s]', pdf_bytes))


class PcmCalculationTests(SimpleTestCase):
    def test_sampling_minutes(self):
        self.assertEqual(sampling_minutes(PcmSample(time_in=time(8, 0), time_out=time(12, 30))), 270)
        self.assertEqual(sampling_minutes(PcmSample(time_in=time(23, 0), time_out=time(1, 0))), 120)  # past midnight
        self.assertIsNone(sampling_minutes(PcmSample(time_in=time(8, 0))))

    def test_average_flow_rate(self):
        sample = PcmSample(flow_rate_before=Decimal('10.00'), flow_rate_after=Decimal('9.80'))
        self.assertEqual(average_flow_rate(sample), Decimal('9.9'))
        self.assertIsNone(average_flow_rate(PcmSample(flow_rate_before=Decimal('10.00'))))

    def test_sample_volume(self):
        sample = PcmSample(time_in=time(8, 0), time_out=time(12, 0),
                           flow_rate_before=Decimal('10.00'), flow_rate_after=Decimal('9.80'))
        self.assertEqual(calculate_sample_volume(sample), Decimal('2376.00'))
        self.assertIsNone(calculate_sample_volume(PcmSample(time_in=time(8, 0), time_out=time(12, 0))))

    def test_fiber_results(self):
        # 25.5 / (100 * 0.00785) = 32.48 f/mm², 32.48 * 385 / (2376 * 1000) = 0.005 f/cc
        self.assertEqual(calculate_fiber_results(Decimal('25.5'), 100, Decimal('2376')),
                         (Decimal('32.48'), Decimal('0.005')))
        self.assertEqual(calculate_fiber_results(Decimal('25.5'), 100, None), (Decimal('32.48'), None))
        self.assertEqual(calculate_fiber_results(None, 100, Decimal('2376')), (None, None))
        self.assertEqual(calculate_fiber_results(Decimal('5'), 0, Decimal('2376')), (None, None))


class ReportFormattingTests(SimpleTestCase):
    def test_fmt_number(self):
        self.assertEqual(fmt_number(Decimal('2376.00')), '2376')
        self.assertEqual(fmt_number(Decimal('9.90')), '9.9')
        self.assertEqual(fmt_number(Decimal('0.0')), '0')
        self.assertEqual(fmt_number(20), '20')
        self.assertEqual(fmt_number(None), '')

    def test_fmt_fixed(self):
        self.assertEqual(fmt_fixed(Decimal('0.01'), 3), '0.010')
        self.assertEqual(fmt_fixed(None, 3), '')

    def test_highlight_limit(self):
        self.assertTrue(is_above_limit(PcmSample(fiber_per_cub_cm=Decimal('0.010'))))
        self.assertFalse(is_above_limit(PcmSample(fiber_per_cub_cm=Decimal('0.009'))))
        self.assertFalse(is_above_limit(PcmSample()))

    def test_column_values(self):
        analysed = PcmSample(lab_sample='26-0001-1', client_sample='C-1', location='Room 101', iwa_owa=1,
                             time_in=time(8, 0), time_out=time(12, 0),
                             flow_rate_before=Decimal('10.00'), flow_rate_after=Decimal('9.80'),
                             sample_volume=Decimal('2376.00'), amount_fibers=Decimal('25.5'), fields=100,
                             fiber_per_mm=Decimal('32.48'), fiber_per_cub_cm=Decimal('0.005'))
        self.assertEqual([column.value(analysed) for column in COLUMNS],
                         ['26-0001-1', 'C-1', 'Room 101', 'IWA', '08:00', '12:00', 240,
                          '9.9', '2376', '25.5', 100, '32.48', '0.005'])

        not_counted = PcmSample(lab_sample='26-0001-2', fields=100)
        self.assertEqual([column.value(not_counted) for column in COLUMNS],
                         ['26-0001-2', '', '', None, '', '', None, '', '', '', None, '', ''])


class PcmReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('analyst', password='x', first_name='Ann', last_name='Lee')
        main_project = MainProject.objects.create(
            lab_id='26-0001', project_name='School', project_address='1 Main St',
            company=Company.objects.create(name='ACME'),
            project_type=MainTypeAnalysis.PCM,
            turn_around_time=TurnAroundTime.objects.create(hour=24, label='24h'),
            status=ProjectStatus.objects.create(status_name='New'),
            number_samples=2,
        )
        cls.pcm_project = PcmProject.objects.create(project=main_project, analyst=cls.user, type_sampling=2)

    def add_samples(self, count, **fields):
        PcmSample.objects.bulk_create(
            PcmSample(pcm_project=self.pcm_project, row_number=i, lab_sample=f'26-0001-{i}', **fields)
            for i in range(1, count + 1)
        )

    def test_report_with_samples(self):
        # text from the database must not break ReportLab markup
        self.add_samples(3, location='Room A&B <north>\nfloor 2', amount_fibers=Decimal('12.5'),
                         fiber_per_mm=Decimal('15.92'), fiber_per_cub_cm=Decimal('0.012'))
        pdf = PcmReportGenerator(self.pcm_project).build().getvalue()
        self.assertTrue(pdf.startswith(b'%PDF-'))
        self.assertEqual(page_count(pdf), 1)

    def test_report_without_samples(self):
        pdf = PcmReportGenerator(self.pcm_project).build().getvalue()
        self.assertEqual(page_count(pdf), 1)

    def test_long_report_continues_on_next_pages(self):
        self.add_samples(60, location='Hallway')
        pdf = PcmReportGenerator(self.pcm_project).build().getvalue()
        self.assertGreater(page_count(pdf), 1)

    def test_report_view(self):
        self.add_samples(2)
        self.client.force_login(self.user)
        response = self.client.get(reverse('pcm:generate_pcm_report', args=[self.pcm_project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('PCM_report_26-0001.pdf', response['Content-Disposition'])
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))

    def test_report_view_for_deleted_project(self):
        MainProject.objects.filter(pk=self.pcm_project.project_id).update(deleted=True)
        self.client.force_login(self.user)
        response = self.client.get(reverse('pcm:generate_pcm_report', args=[self.pcm_project.id]))
        self.assertEqual(response.status_code, 404)
