"""
PCM air sample report (NIOSH 7400) as a PDF.

Usage (see pcm/views.py):
    pdf_buffer = PcmReportGenerator(pcm_project).build()

Where to change things:
    table columns ............. COLUMNS
    notes under the table ..... NOTES
    yellow highlighting ....... FIBERS_PER_CC_LIMIT
    lab address, logo, font ... report_generator/common.py

Nothing is calculated here twice: minutes and flow rate come from pcm/pcm_table_logic.py,
volume, fibers/mm² and fibers/cc are the values saved on the samples.
"""
from decimal import Decimal

from django.utils import timezone
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Spacer

from pcm.models import PcmSample
from pcm.pcm_table_logic import FIELD_AREA_MM2, FILTER_COLLECTION_AREA_MM2, average_flow_rate, sampling_minutes
from report_generator.common import (
    LAB_INFO,
    ReportColumn,
    build_pdf,
    details_table,
    draw_page_header,
    fmt_date,
    fmt_fixed,
    fmt_number,
    fmt_time,
    notes_block,
    samples_table,
    signature_block,
)

TITLE = 'AIR SAMPLE ANALYSIS REPORT'
SUBTITLE = 'Phase Contrast Microscopy (PCM)'

# fibers/cc at or above this value are painted yellow; None turns highlighting off
FIBERS_PER_CC_LIMIT = Decimal('0.01')


# ---------- Cell values that need more than one field ----------
def work_area_label(sample):
    return sample.get_iwa_owa_display() if sample.iwa_owa else None

def fields_counted(sample):
    # 'fields' defaults to 100, so it is shown only for samples that were counted
    return sample.fields if sample.amount_fibers is not None else None

def is_above_limit(sample):
    return (FIBERS_PER_CC_LIMIT is not None
            and sample.fiber_per_cub_cm is not None
            and sample.fiber_per_cub_cm >= FIBERS_PER_CC_LIMIT)


# ---------- Table: one entry per column, widths are relative ----------
COLUMNS = [
    ReportColumn('Lab\nSample ID',     0.95 * inch, lambda s: s.lab_sample),
    ReportColumn('Client\nSample ID',  0.85 * inch, lambda s: s.client_sample),
    ReportColumn('Sample Location',    2.40 * inch, lambda s: s.location),
    ReportColumn('IWA /\nOWA',         0.45 * inch, work_area_label),
    ReportColumn('Time\nOn',           0.50 * inch, lambda s: fmt_time(s.time_in)),
    ReportColumn('Time\nOff',          0.50 * inch, lambda s: fmt_time(s.time_out)),
    ReportColumn('Total\nMinutes',     0.55 * inch, sampling_minutes),
    ReportColumn('Avg Flow\nL/min',    0.60 * inch, lambda s: fmt_number(average_flow_rate(s))),
    ReportColumn('Volume\nL',          0.65 * inch, lambda s: fmt_number(s.sample_volume)),
    ReportColumn('Fibers\nCounted',    0.55 * inch, lambda s: fmt_number(s.amount_fibers)),
    ReportColumn('Fields\nCounted',    0.55 * inch, fields_counted),
    ReportColumn('Fibers/mm²',         0.70 * inch, lambda s: fmt_fixed(s.fiber_per_mm, 2)),
    ReportColumn('Fibers/cc',          0.70 * inch, lambda s: fmt_fixed(s.fiber_per_cub_cm, 3),
                 highlight=is_above_limit),
]

NOTES = [
    'PCM - Phase Contrast Microscopy, NIOSH Method 7400 ("A" counting rules). '
    'PCM does not distinguish asbestos from other fibers.',
    'IWA - Inside Work Area. OWA - Outside Work Area.',
    'Volume = average flow rate × sampling time. '
    f'Fibers/mm² = fibers counted / (fields counted × {FIELD_AREA_MM2} mm²). '
    f'Fibers/cc = fibers/mm² × {FILTER_COLLECTION_AREA_MM2} mm² / (volume × 1000).',
    'The results relate only to the items tested.',
    'The report shall not be reproduced without the written approval of the laboratory.',
]


class PcmReportGenerator:
    def __init__(self, pcm_project):
        self.project = pcm_project
        self.main_project = pcm_project.project     # client, address, lab id
        self.samples = list(PcmSample.objects.filter(pcm_project=pcm_project).order_by('row_number', 'id'))
        self.report_date = timezone.localdate()

    def build(self):
        """Returns the PDF as BytesIO, ready for FileResponse."""
        story = [
            samples_table(COLUMNS, self.samples),
            Spacer(1, 0.15 * inch),
            # details, signature and notes are never split between pages
            KeepTogether([
                details_table(self._details_rows()),
                Spacer(1, 0.25 * inch),
                signature_block(),
                *notes_block(NOTES),
            ]),
        ]
        return build_pdf(story, self._draw_page_header, title=f'PCM Report {self.main_project.lab_id}')

    def _draw_page_header(self, canvas_obj, doc):
        main = self.main_project
        draw_page_header(
            canvas_obj, TITLE, SUBTITLE,
            client_rows=[
                ('Client Name:',      main.company.name),
                ('Building Address:', main.project_address),
                ('Client Project:',   f'{main.project_name}; Sampled By: {self._sampled_by()}'),
            ],
            report_rows=[
                f'Report ID: {main.lab_id}',
                f'Report Date: {fmt_date(self.report_date)}',
                LAB_INFO['elap'],
            ],
        )

    def _details_rows(self):
        project = self.project
        type_sampling = project.get_type_sampling_display() if project.type_sampling else ''
        return [
            [f'Date Collected: {fmt_date(project.date_collect)}',
             f'Date Received: {fmt_date(self.main_project.date_registered)}',
             f'Date Analyzed: {fmt_date(project.date_analyze)}'],
            [f'Type of Sampling: {type_sampling}',
             f'Work Area: {project.work_area}',
             f'Rotometer: {project.rotometer or ""}'],
            [f'Analyzed By: {self._analyst_name()}'],
        ]

    def _sampled_by(self):
        return self.project.technician or self.main_project.technician or ''

    def _analyst_name(self):
        analyst = self.project.analyst
        if analyst is None:
            return ''
        return analyst.get_full_name() or analyst.username
