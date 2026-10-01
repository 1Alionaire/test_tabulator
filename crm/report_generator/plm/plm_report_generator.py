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

class VerticalText(Flowable):
    """Text, повёрнутый на 90°. Поддерживает многострочность через '\\n'."""

    def __init__(self, text, font_name='TimesNR-Bold', font_size=7,
                 padding=2, leading=None):
        super().__init__()
        self.lines = text.split('\n')
        self.font_name = font_name
        self.font_size = font_size
        self.padding = padding
        # межстрочный интервал; по умолчанию ~1.15 от размера шрифта
        self.leading = leading if leading is not None else font_size * 1.15

    def wrap(self, avail_w, avail_h):
        # высота ячейки = длина самой длинной строки текста
        max_line_w = max(
            stringWidth(line, self.font_name, self.font_size)
            for line in self.lines
        )
        # ширина ячейки растёт с количеством строк
        self.width = self.leading * len(self.lines) + self.padding * 2
        self.height = max_line_w + self.padding * 2
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.rotate(90)
        c.setFont(self.font_name, self.font_size)
        for i, line in enumerate(self.lines):
            # baseline i-й строки = слева направо в исходной ячейке
            baseline_x_old = self.padding + self.font_size + i * self.leading
            c.drawString(self.padding, -baseline_x_old, line)
        c.restoreState()

class NumberedCanvas(canvas.Canvas):
    """
    Canvas, который откладывает страницы до save(), чтобы узнать их общее
    число и нарисовать 'Page X of Y' (футер может уйти на отдельную страницу).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.setFont('TimesNR-Bold', 9)
            self.drawCentredString(PAGE_SIZE[0] / 2, BOTTOM_MARGIN / 2,
                                   f'Page {self._pageNumber} of {total_pages}')
            super().showPage()
        super().save()

# ---- Параметры страницы ----
SAMPLES_PER_PAGE = 20
PAGE_SIZE = landscape(letter)       # широкая таблица — нужна альбомная
LEFT_MARGIN = RIGHT_MARGIN = 0.4 * inch
TOP_MARGIN = 1.30 * inch            # оставляем место под шапку клиента
BOTTOM_MARGIN = 0.4 * inch

LAB_INFO = {
    'name': 'ALLAB',
    'address_line1': '1544 East 13th Street',
    'address_line2': 'Brooklyn, NY 11230',
    'phone': 'Phone: (718) 864-3666',
    'elap': 'NYS-DOH ELAP # 12118',
    'logo_path': str(SCRIPT_DIR / 'allab_logo.png'),              # путь к PNG логотипа, None если пока нет
}

# названия для отчёта (в SampleASbestosType.label есть опечатка 'Anthophillite')
asbestos_names_dict = {
    SampleASbestosType.Chry: 'Chrysotile',
    SampleASbestosType.Amo: 'Amosite',
    SampleASbestosType.Croc: 'Crocidolite',
    SampleASbestosType.Trem: 'Tremolite',
    SampleASbestosType.Act: 'Actinolite',
    SampleASbestosType.Anth: 'Anthophyllite',
}

# методы, у которых есть TEM-анализ (как в api_get_tem_analysis_table)
TEM_METHODS = (SampleMethod.Sample1984, SampleMethod.Sample1986, SampleMethod.Sample1994)

# статусы результата по асбесту
NAD, TRACE, POSITIVE, NOT_ANALYZED = 'NAD', 'TRACE', 'POSITIVE', 'NOT_ANALYZED'

def fmt_num(value):
    """Число → строка. None и 0 → пустая строка."""
    if value is None or value == 0:
        return ''
    # убираем хвостовые нули у Decimal: 5.60 → 5.6
    return f'{float(value):g}'

def fmt_date(value):
    return f'{value:%m/%d/%Y}' if value else ''

def weight_value(s, field):
    """org / residue / caco3 хранятся в PlmSampleWeight, которого может не быть."""
    return getattr(s.weight, field) if s.weight else None

def asb_status(asb_type, asb_percent):
    if asb_type == SampleASbestosType.NotAnalyzed:
        return NOT_ANALYZED
    if asb_type not in asbestos_names_dict:     # None или NAD
        return NAD
    if float(asb_percent or 0) > 1:
        return POSITIVE
    return TRACE

def plm_asb_status(s):
    return asb_status(s.asb_type, s.asb_percent)

def tem_asb_status(s):
    status = asb_status(s.tem_asb_type, s.tem_asb_percent)
    # PS (positive stop) — HA уже позитивный, TEM не делали
    if status == NAD and s.tem_na_or_ps == 'PS':
        return NOT_ANALYZED
    return status

def fmt_asb_result(status, asb_type, asb_percent, nad_text='NAD'):
    if status == NAD:
        return nad_text
    if status == NOT_ANALYZED:
        return 'Not Analyzed'
    if status == POSITIVE:
        return f'{fmt_num(asb_percent)}%\n{asbestos_names_dict[asb_type]}'
    return f'Trace\n{asbestos_names_dict[asb_type]}'

def fmt_plm_asb_result(s):
    """PLM Friable — только для 198.1."""
    if s.method != SampleMethod.Sample1981:
        return None
    return fmt_asb_result(plm_asb_status(s), s.asb_type, s.asb_percent)

def fmt_plm_other_fiber(s):
    if s.other_fiber and s.other_fiber_percent:
        return f'{fmt_num(s.other_fiber_percent)}% {s.get_other_fiber_display()}'
    return ''

def fmt_non_fibros(s):
    """Для PLM-метода: доля не-фиброзного материала."""
    if s.method != SampleMethod.Sample1981:
        return None
    asb_percent = float(s.asb_percent or 0)
    other = float(s.other_fiber_percent or 0)
    return f'{fmt_num(100 - other - asb_percent)}%'

def fmt_nob_asb_result(s):
    """PLM NOB — колонка для гравиметрии (198.6)."""
    if s.method != SampleMethod.Sample1986:
        return None
    return fmt_asb_result(plm_asb_status(s), s.asb_type, s.asb_percent,
                          nad_text='Inconclusive NAD')

def fmt_tem_asb_result(s):
    if s.method not in TEM_METHODS:
        return None
    return fmt_asb_result(tem_asb_status(s), s.tem_asb_type, s.tem_asb_percent)

COLUMNS = [
    ('Client\nID',          0.40 * inch, lambda s: s.client_sample,                   False),
    ('LAB ID#',             0.70 * inch, lambda s: s.lab_sample,                      False),
    ('Layer',               0.15 * inch, lambda s: s.layer,                           True),
    ('Sample\nDescription', 1.40 * inch, lambda s: s.description,                     False),
    ('Sample\nLocation',    1.35 * inch, lambda s: s.location,                        False),
    ('HA No.',              0.28 * inch, lambda s: s.homo_area,                       True),
    ('Analytical\nMethod',  0.28 * inch, lambda s: s.get_method_display(),            True),
    ('Color',               0.28 * inch, lambda s: s.color,                           False),
    ('PLM Friable Asbestos % and Type',
                            0.55 * inch, lambda s: fmt_plm_asb_result(s),             False),
    ('Other Fiber Material % and Type',
                            0.55 * inch, lambda s: fmt_plm_other_fiber(s),            False),
    ('Non-Fibros Material %',
                            0.40 * inch, lambda s: fmt_non_fibros(s),                 False),
    ('PLM NOB Asbestos % and Type',
                            0.55 * inch, lambda s: fmt_nob_asb_result(s),             False),
    ('Organic %',           0.28 * inch, lambda s: fmt_num(weight_value(s, 'org')),     True),
    ('Non-organic %',       0.32 * inch, lambda s: fmt_num(weight_value(s, 'residue')), True),
    ('CACO3 %',             0.28 * inch, lambda s: fmt_num(weight_value(s, 'caco3')),   True),
    ('Vermiculite',         0.25 * inch, lambda s: 'ND',                              True),
    ('TEM RESULT Item 198.4',
                            0.50 * inch, lambda s: fmt_tem_asb_result(s),             False),
]

# индексы колонок с результатами — для жёлтой подсветки
PLM_COL, NOB_COL, TEM_COL = 8, 11, 16
SAMPLE_INFO_COLS = (0, 4)           # Client ID … Sample Location

def fit_column_widths(columns, available_width):
    """
    Пропорционально масштабирует ширины колонок, чтобы их сумма
    равнялась available_width. Возвращает список ширин в пунктах.
    """
    raw_widths = [col[1] for col in columns]
    total = sum(raw_widths)
    scale = available_width / total
    return [w * scale for w in raw_widths]

class BulkSampleReportGenerator: # initialize class 
    # Init base class BaseDocTemplate from reportlab.platypus
    def __init__(self, project):
        self.project = project  # input project 
        # parsing all samples 
        self.samples = list( 
            PlmSample.original_samples.filter(plm_project=project)
            .select_related('weight')
            .order_by('row_number', 'id')
        )
        self.buffer = BytesIO() #init binary buffer (it needs for return file)
        self.styles = self._build_styles() #setting fonts and other decorations

    # ---------- Public method. Start building document process ----------
    def build(self):
         # Init base class BaseDocTemplate from reportlab.platypus
        doc = BaseDocTemplate( # init BaseDocTemplate
            self.buffer, # BytesIO, binary buffer, we will fill with document
            pagesize=PAGE_SIZE, #page size - landscape(letter)
            leftMargin=LEFT_MARGIN, #sizes 
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
            onPage=self._draw_page_fram , # render on every page
        )
        doc.addPageTemplates([page_template]) # adding template to basedocument

        story = self._build_story()  #filling document with main info

        #  NumberedCanvas renders page numbers, he needs total amount of samples
        doc.build(story, canvasmaker=NumberedCanvas)

        self.buffer.seek(0) #taking binary document
        return self.buffer

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

    def _build_story(self):
        """Gather flowable-элементы: tables by 20 samples + footer"""
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

    def _build_samples_table(self, samples_chunk): #we put array of samples 
        # --- Table header  ---
        header_row = []
        for title, _, _, is_vertical in COLUMNS: # we going through static array COLUMNS
            if is_vertical: #if vertical option for column element? 
                header_row.append(VerticalText(title)) #call special function for vertical text 
            else:
                header_row.append( #add title to header
                    Paragraph(title.replace('\n', '<br/>'), self.styles['header'])
                )
        data = [header_row]

        # (col_from, col_to, row) — ячейки с жёлтым фоном
        yellow_cells = [] # init array of yellow cells
        # --- Table body ---
        for row_idx, sample in enumerate(samples_chunk, start=1): # go through every sample 
            row = [] # init row   
            for title, width, extractor, is_vertical in COLUMNS: # we going through static array COLUMNS
                value = extractor(sample) or '' #extractor - function that get value from sample
                row.append(Paragraph(
                    str(value).replace('\n', '<br/>'), # replace tag to special tab
                    self.styles['cell'], #attach style for cell 
                ))
            data.append(row) # append row 

            # collecting all asbestos result. key = column, value = asb result
            statuses = {}
            if sample.method == SampleMethod.Sample1981:
                statuses[PLM_COL] = plm_asb_status(sample)
            if sample.method == SampleMethod.Sample1986:
                statuses[NOB_COL] = plm_asb_status(sample)
            if sample.method in TEM_METHODS:
                statuses[TEM_COL] = tem_asb_status(sample)

            # Trace / Positive / Not Analyzed — append in yellow cells array
            for col, status in statuses.items():
                if status != NAD:
                    yellow_cells.append((col, col, row_idx))

            # positive or Not Analyzed — mark also info about sample
            if any(status in (POSITIVE, NOT_ANALYZED) for status in statuses.values()):
                yellow_cells.append((*SAMPLE_INFO_COLS, row_idx))

        # make column fit
        available = PAGE_SIZE[0] - LEFT_MARGIN - RIGHT_MARGIN
        col_widths = fit_column_widths(COLUMNS, available)

        # fix header height — or vertical text will be cut
        header_height = 0.75 * inch   # fit to longest header
        row_heights = [header_height] + [0.28 * inch] * (len(data) - 1)  #adjust row height

        table = Table(data, colWidths=col_widths, rowHeights=row_heights, repeatRows=1) #make table
        # making base style
        base_set_style = [ 
            ('GRID',           (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND',     (0, 0), (-1, 0),  colors.lightgrey),
            ('VALIGN',         (0, 0), (-1, 0),  'MIDDLE'),  # шапка — по нижнему краю
            ('VALIGN',         (0, 1), (-1, -1), 'MIDDLE'),  # данные — по центру
            ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING',    (0, 0), (-1, -1), 2),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 2),
            ('TOPPADDING',     (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 2),
        ]

        # coloring yellow color positive cells 
        for col_from, col_to, row in yellow_cells:
            base_set_style.append(('BACKGROUND', (col_from, row), (col_to, row), colors.yellow))

        # setting table style
        table.setStyle(TableStyle(base_set_style))

        return table

    def _build_footer_block(self):
        """Блок под последней таблицей: даты + подпись + примечания."""
        p = self.project
        elements = []

        # --- Даты ---
        dates_row = [[
            Paragraph(f'<b>Date Collected:</b> {fmt_date(p.date_collect)}', self.styles['cell']),
            Paragraph(f'<b>Date Received:</b> {fmt_date(p.date_receive)}',  self.styles['cell']),
            Paragraph(f'<b>Date of Analyses:</b> {fmt_date(p.date_analyze)}', self.styles['cell']),
        ]]
        col_w = (PAGE_SIZE[0] - LEFT_MARGIN - RIGHT_MARGIN) / 3
        dates_table = Table(dates_row, colWidths=[col_w] * 3)
        dates_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(dates_table)
        elements.append(Spacer(1, 0.25 * inch))

        available = PAGE_SIZE[0] - LEFT_MARGIN - RIGHT_MARGIN
        image_width = 1.5 * inch
        label_width = 0.9 * inch                       # ширина под "Lab Director:"
        spacer_width = available - label_width - image_width

        sig_table = Table(
            [[
                '',                                                            # распорка
                Paragraph('<b>Lab Director:</b>', self.styles['cell']),       # лейбл
                Image(
                    str(SCRIPT_DIR / 'lab_director_sign.jpg'),
                    width=image_width, height=0.5 * inch,
                    kind='proportional',
                ),                                                             # подпись
            ]],
            colWidths=[spacer_width, label_width, image_width],
        )
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',  (1, 0), (1, 0), 'RIGHT'),     # лейбл прижат к правому краю своей ячейки
            ('ALIGN',  (2, 0), (2, 0), 'LEFT'),      # картинка прижата к левому краю своей
            # GRID/BOX не ставим — таблица невидима
        ]))
        elements.append(sig_table)

        # --- Примечания ---
        notes = [
            'PLM - Polarized-Light Microscopy. NOB - Non-Friable Organically Bound Materials. TEM - Transmission Electron Microscopy',
            '198.1 - Method Item 198.1 of ELAP Certification Manual. 198.6 - Method Item 198.6 of ELAP Certification Manual. 198.4 - Method Item 198.4 of ELAP Certification Manual.',
            'EPA 600 - Method EPA 600/M4/82/020 NJ EPA - Method EPA 600/R-93-116',
            'ND - Not Detected NAD - No asbestos detected Trace - Inconclusive. Asbestos detected at 1% or less.',
            'Samples with inconclusive results must not be interpreted as being non-asbestos.',
            'Quantitative transmission electron microscopy is currently the only method that can be used to determine if this material can be considered or treated as non-asbestos containing.',
            'Results NAD or TRACE by PLM are inconclusive.',
            'The results relate only to the items tested. Samples will be stored for sixty (60) days.',
            'The report shall not be reproduced without the written approval of the laboratory.',
            "The currently approved methods for the analysis of SM-V include NYS DOH Item 198.8 and RJ Lee Group's Method 055.",
        ]

        for text in notes:
            elements.append(Paragraph(text, self.styles['note']))

        elements.append(Spacer(1, 0.1 * inch))
        return elements
