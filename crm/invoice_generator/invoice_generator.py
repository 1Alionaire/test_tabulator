# services/report_generator.py
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Table, TableStyle, PageBreak, Spacer, Image,
)
from plm.models import PlmSample, SampleMethod, SampleASbestosType
from reportlab.platypus import Flowable
from reportlab.pdfbase.pdfmetrics import stringWidth
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

SCRIPT_DIR = Path(__file__).resolve().parent

pdfmetrics.registerFont(TTFont('TimesNR-Bold',  str(SCRIPT_DIR / 'Times New Roman_bold.ttf')))

pdfmetrics.registerFontFamily(
    'TimesNR',
    normal='TimesNR',
    bold='TimesNR-Bold',
    italic='TimesNR-Italic',
    boldItalic='TimesNR-BoldItalic',
)

# ---- Параметры страницы ----
SAMPLES_PER_PAGE = 20
PAGE_SIZE = landscape(letter)       # широкая таблица — нужна альбомная
LEFT_MARGIN = RIGHT_MARGIN = 0.4 * inch
TOP_MARGIN = 2.30 * inch            # оставляем место под шапку клиента
BOTTOM_MARGIN = 0.4 * inch

LAB_INFO = {
    'name': 'ALLAB',
    'address_line1': '1544 East 13th Street',
    'address_line2': 'Brooklyn, NY 11230',
    'phone': 'Phone: (718) 864-3666',
    'elap': 'NYS-DOH ELAP # 12118',
    'logo_path': str(SCRIPT_DIR / 'allab_logo.png'),              # путь к PNG логотипа, None если пока нет
}

class InvoiceGenerator:
    def __init__(self, project, input_data): # initialize class 
        self.project = project # input project 
        self.buffer = BytesIO() # init binary buffer (it needs for return file)
        self.styles = self._build_styles() # build fonts and other decorations


    # ---------- Публичный метод ----------
    def build(self):
        # Init base class BaseDocTemplate from reportlab.platypus
        doc = BaseDocTemplate( # init BaseDocTemplate
            self.buffer, # BytesIO
            pagesize=PAGE_SIZE, #page size - landscape(letter)
            leftMargin=LEFT_MARGIN, 
            rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            title=f'Bulk Sample Report {self.project.lab_id}',
        )

        # Frame — rectangle, where put content (tables, text)
        content_frame = Frame(
            doc.leftMargin, doc.bottomMargin, #frame margins from doc object
            doc.width, doc.height,
            id='content', #frame id
            showBoundary=0,
        )

        # PageTemplate contain logic of rendering all elements excluding main info (logos, signs etc)
        page_template = PageTemplate(
            id='main',
            frames=[content_frame], # Frame
            onPage=self._draw_page_frame,   # render on every page
        )

        doc.addPageTemplates([page_template]) # adding template to basedocument

        story = self._build_story() #filling document with main info

        # номер страницы рисует NumberedCanvas — ему нужно общее число страниц
        doc.build(story)

        self.buffer.seek(0)
        return self.buffer

    def _build_story(self):
        """Gather flowable-elements: tables by 20 samples + footer"""
        story = [] # init array
        chunks = [ #fraction all samples into 20 portion samples(matrix of samples, where row amount = total//20, column amount = 20)
            self.samples[i:i + SAMPLES_PER_PAGE]
            for i in range(0, len(self.samples), SAMPLES_PER_PAGE)
        ]
        # если сэмплов нет — всё равно одна пустая таблица, чтобы отрисовалась шапка
        if not chunks:
            chunks = [[]]

        for idx, chunk in enumerate(chunks): #going through matrix
            story.append(self._build_samples_table(chunk)) #build table for 20 samples
            is_last = (idx == len(chunks) - 1) # checking is last chunk or no
            if not is_last: 
                story.append(PageBreak()) # adding a page break 

        # build for last piece of table 
        story.append(Spacer(1, 0.15 * inch))
        story.extend(self._build_footer_block()) # build footer block
        return story

    def _build_styles(self):
        base = getSampleStyleSheet()
        return {
            'cell': ParagraphStyle(
                'cell', parent=base['Normal'],
                fontSize=8, leading=8, alignment=TA_CENTER, fontName='TimesNR-Bold',
            ),
            'cell_bold': ParagraphStyle(
                'cell_bold', parent=base['Normal'],
                fontSize=7, leading=8, alignment=TA_CENTER,
                fontName='TimesNR-Bold',
            ),
            'header': ParagraphStyle(
                'header', parent=base['Normal'],
                fontSize=7, leading=8, alignment=TA_CENTER,
                fontName='TimesNR-Bold',
            ),
            'note': ParagraphStyle(
                'note', parent=base['Normal'],
                fontSize=4.5, leading=7.5,
            ),
            'signature': ParagraphStyle(
                'signature', parent=base['Normal'],
                fontName='TimesNR-Bold', fontSize=9, leading=11,
                alignment=TA_LEFT,
                leftIndent=6.5 * inch,    # ← вот эта ручка
            )
        }

    def _draw_page_frame(self, canvas_obj, doc):
        """Callback, который ReportLab вызывает для каждой страницы."""
        canvas_obj.saveState()
        page_w, page_h = PAGE_SIZE
        main_project = self.project.project     # MainProject: клиент, адрес, lab_id

        # --- Логотип (если есть) ---
        if LAB_INFO['logo_path']:
            canvas_obj.drawImage(
                LAB_INFO['logo_path'],
                LEFT_MARGIN, page_h - 0.8 * inch,
                width=0.8 * inch, height=0.5 * inch,
                preserveAspectRatio=True, mask='auto',
            )

        # --- Центральный титул ---
        canvas_obj.setFont('TimesNR-Bold', 14)
        canvas_obj.drawCentredString(page_w / 2, page_h - 0.45 * inch,
                                     'BULK SAMPLE ANALYSIS REPORT')
        canvas_obj.setFont('TimesNR-Bold', 10)
        canvas_obj.drawCentredString(page_w / 2, page_h - 0.62 * inch,
                                     'Laboratory Report')

        # --- Адрес лаборатории (правый верх) ---
        canvas_obj.setFont('TimesNR-Bold', 8)
        right_x = page_w - RIGHT_MARGIN
        canvas_obj.drawRightString(right_x, page_h - 0.40 * inch, LAB_INFO['address_line1'])
        canvas_obj.drawRightString(right_x, page_h - 0.52 * inch, LAB_INFO['address_line2'])
        canvas_obj.drawRightString(right_x, page_h - 0.64 * inch, LAB_INFO['phone'])

        # --- Инфо о клиенте (лево) ---
        y = page_h - 0.95 * inch
        row_h = 0.15 * inch

        canvas_obj.setFont('TimesNR-Bold', 9)
        canvas_obj.drawString(LEFT_MARGIN, y,               'Client Name:')
        canvas_obj.drawString(LEFT_MARGIN, y - row_h,       'Building Address:')
        canvas_obj.drawString(LEFT_MARGIN, y - 2 * row_h,   'Client Project:')

        canvas_obj.setFont('TimesNR-Bold', 9)
        label_offset = 1.3 * inch
        canvas_obj.drawString(LEFT_MARGIN + label_offset, y,
                              main_project.company.name)
        canvas_obj.drawString(LEFT_MARGIN + label_offset, y - row_h,
                              main_project.project_address)
        canvas_obj.drawString(
            LEFT_MARGIN + label_offset, y - 2 * row_h,
            f'{main_project.project_name}; Sampled By: {main_project.technician or ""}',
        )

        # --- Инфо о репорте (право) ---
        canvas_obj.setFont('TimesNR-Bold', 9)
        canvas_obj.drawRightString(right_x, y,             f'Report ID: {main_project.lab_id}')
        canvas_obj.drawRightString(right_x, y - row_h,     f'Report Date: {fmt_date(self.project.date_report)}')
        canvas_obj.drawRightString(right_x, y - 2 * row_h, LAB_INFO['elap'])

        # номер страницы ('Page X of Y') рисует NumberedCanvas.save()

        canvas_obj.restoreState()

    