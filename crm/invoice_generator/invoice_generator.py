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
from finance.models import Company
from plm.models import (
    PlmProject,
    PlmSample,
    SampleMethod,
    SampleASbestosType,
)
from reportlab.lib.colors import HexColor
from decimal import Decimal, ROUND_HALF_UP
from main.models import MainTypeAnalysis

payment_text = '''Make all checks payable to: ALLAB Analytical Labs
Total due in <30> days. Overdue accounts subject to a service charge of <1.5>% per month.'''

# color background - 
ROW_SHADE = colors.HexColor("#DBE5F1")
SCRIPT_DIR = Path(__file__).resolve().parent

# шрифт лежит рядом с генератором отчётов — регистрируем сами, не полагаясь на порядок импортов
FONT_PATH = SCRIPT_DIR.parent / 'report_generator' / 'plm' / 'Times New Roman_bold.ttf'
pdfmetrics.registerFont(TTFont('TimesNR-Bold', str(FONT_PATH)))
pdfmetrics.registerFontFamily('TimesNR', normal='TimesNR-Bold', bold='TimesNR-Bold')

# ---- Sheet parameters ----
PAGE_SIZE = letter    
LEFT_MARGIN = RIGHT_MARGIN = 0.4 * inch
TOP_MARGIN = 2.70 * inch            
BOTTOM_MARGIN = 0.4 * inch
RECORDS_PER_PAGE = 20

# путь к PNG логотипа, None если пока нет
LAB_INFO = {
    'name': 'ALLAB',
    'address_line1': '1544 East 13th St.',
    'address_line2': 'Brooklyn, NY 11230',
    'phone': 'Phone Number: (718) 864-3666',
    'elap': 'NYS-DOH ELAP # 12118',
    'logo_path': str(SCRIPT_DIR / 'allab_logo.png'),  
    'email':'Email: allabcrue@gmailcom',
    'website':'Website: allab.org'
}

def fmt_money(value):
    """6 -> "$6.00", 1234.5 -> "$1,234.50", -5 -> "-$5.00", None -> ""."""
    if value is None or value == "":
        return ""
    v = Decimal(str(value)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return f"-${abs(v):,.2f}" if v < 0 else f"${v:,.2f}"

class DataForInvoiceGenerator:
    def __init__(self, projects):
        self.projects = projects
        self.company = Company.objects.get(pk=projects[0].company.id)
        self.price_json = ''

    def build_total_info(self):
        result_array = []
        for project in self.projects:
            if project.project_type in [MainTypeAnalysis.Bulk, MainTypeAnalysis.BulkTEM, MainTypeAnalysis.TEM]:
                result_array.extend(self.parse_info_from_plm_project(project))
                # for sample in self.parse_info_from_plm_project(project):
                #     result_array.append(sample)

        return result_array

    def parse_info_from_plm_project(self, input_project):
        array = []
        plm_count = 0
        nob_count = 0 
        prep_count = 0
        tem_count = 0 
        
        plm_project = PlmProject.objects.get(project=input_project)

        samples = list( 
            PlmSample.original_samples.filter(plm_project=plm_project)
            .select_related('weight')
            .order_by('row_number', 'id')
            .values('asb_type', 'method', 'tem_asb_type' )
        )

        for sample in samples:
            if sample['method'] == SampleMethod.Sample1981:
                if sample['asb_type'] != SampleASbestosType.NotAnalyzed:
                    plm_count += 1

            if sample['method'] == SampleMethod.Sample1986:
                if sample['asb_type'] != SampleASbestosType.NotAnalyzed:
                    nob_count += 1
                else:
                    prep_count += 1
                    
                if sample['tem_asb_type'] != SampleASbestosType.NotAnalyzed:
                    tem_count += 1

            if sample['method'] == SampleMethod.Sample1984:
                if sample['tem_asb_type'] != SampleASbestosType.NotAnalyzed:
                    tem_count += 1

            if sample['method'] == SampleMethod.Sample1994:
                if sample['tem_asb_type'] != SampleASbestosType.NotAnalyzed:
                    tem_count += 1

        if plm_count > 0:
            array.append({
                        'lab_id': '',
                        'project_name': '', 
                        'project_address': '',
                        'type': 'PLM',
                        'count': plm_count, 
                        'unit_price': self.company.plm_price,
                        'total': self.company.plm_price * plm_count
                    })

        if nob_count > 0:
            array.append({
                        'lab_id': '',
                        'project_name': '', 
                        'project_address': '',
                        'type': 'PLM_NOB',
                        'count': nob_count, 
                        'unit_price': self.company.nob_price,
                        'total': self.company.nob_price * nob_count
                    })

        if prep_count > 0:
            array.append({
                        'lab_id': '',
                        'project_name': '', 
                        'project_address': '',
                        'type': 'Prep.Charge',
                        'count': prep_count, 
                        'unit_price': self.company.prep_nob_price,
                        'total': self.company.prep_nob_price * prep_count
                    })

        if tem_count > 0:
            array.append({
                        'lab_id': '',
                        'project_name': '', 
                        'project_address': '',
                        'type': 'NOB_TEM',
                        'count': tem_count, 
                        'unit_price': self.company.tem_price,
                        'total': self.company.tem_price * tem_count
                })

        # проект без оплачиваемых сэмплов (например, все Not analyzed) — строк нет
        if array:
            array[0]['lab_id'] = input_project.lab_id
            array[0]['project_name'] = input_project.project_name
            array[0]['project_address'] = input_project.project_address

        return array

   
class InvoiceGenerator:
    def __init__(self, projects, invoice_info=None): # initialize class 
        self.projects = projects #
        self.invoice_data = DataForInvoiceGenerator(projects).build_total_info() #
        self.buffer = BytesIO() # init binary buffer (it needs for return file)
        self.styles = self._build_styles() # build fonts and other decorations
        self.company_name = Company.objects.get(pk=projects[0].company.id).name
        if invoice_info is None:
            plm_project = PlmProject.objects.get(project=projects[0])
            self.invoice_number = projects[0].lab_id
            self.invoice_date = str(plm_project.date_report)
            self.invoice_for = None

    def _count_total(self):
        return sum([element['total'] for element in self.invoice_data] )

    def build(self):
        # Init base class BaseDocTemplate from reportlab.platypus
        doc = BaseDocTemplate( # init BaseDocTemplate
            self.buffer, # BytesIO
            pagesize=PAGE_SIZE, #page size - landscape(letter)
            leftMargin=LEFT_MARGIN, 
            rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            title=f'Invoice',)

        # Frame — rectangle, where put content (tables, text)
        content_frame = Frame(
            doc.leftMargin, doc.bottomMargin, #frame margins from doc object
            doc.width, doc.height,
            leftPadding=0, rightPadding=0,
            id='content', #frame id
            showBoundary=0,
        )

        # PageTemplate contain logic of rendering all elements excluding main info (logos, signs etc)
        page_template = PageTemplate(
            id='main',
            frames=[content_frame], # Frame 
            onPage=self._draw_page_frame , # render on every page
        )
        doc.addPageTemplates([page_template]) # adding template to basedocument

        story = self._build_story()  #filling document with main info
        
        #  NumberedCanvas renders page numbers, he needs total amount of samples
        doc.build(story)

        self.buffer.seek(0) #taking binary document
        return self.buffer

    def _draw_page_frame(self, canvas_obj, doc):
        canvas_obj.saveState()
        page_w, page_h = PAGE_SIZE

        # одна рамка для прямоугольника и логотипа
        box_x = LEFT_MARGIN
        box_y = page_h - 1.4 * inch
        box_w = 7.5 * inch
        box_h = 0.75 * inch
        pad = 0.05 * inch              # отступ логотипа от рамки

        canvas_obj.setFillColor(HexColor("#366092"))
        canvas_obj.rect(LEFT_MARGIN, page_h - 1.4 * inch, box_w, box_h, stroke=0, fill=1)

        # --- Логотип (если есть): по высоте рамки, прижат влево ---
        if LAB_INFO['logo_path']:
            canvas_obj.drawImage(
                LAB_INFO['logo_path'],
                LEFT_MARGIN , page_h - 1.4 * inch + pad,
                width=box_w - 2 * pad, height=box_h - 2 * pad,
                preserveAspectRatio=True, anchor='w', mask='auto',
            )
        canvas_obj.restoreState()

        canvas_obj.setFillColor(HexColor("#95B3D7"))
        canvas_obj.rect(box_x, page_h - 1.90 * inch, box_w, 0.5 * inch, stroke=0, fill=1)

        canvas_obj.setFillColor(HexColor("#020202"))
        canvas_obj.setFont("Times-Roman", 8)
        canvas_obj.drawString(35, 682, LAB_INFO['address_line1'])
        canvas_obj.drawString(35, 672, LAB_INFO['address_line2'])
        canvas_obj.drawString(235, 682, LAB_INFO['phone'])
        canvas_obj.drawString(435, 682, LAB_INFO['email'])
        canvas_obj.drawString(435, 672, LAB_INFO['website'])

        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(35, 642, 'Bill To:')
        canvas_obj.drawString(100, 642, self.company_name)
        
        canvas_obj.drawString(35, 630, 'Address:')
        canvas_obj.drawString(35, 610, 'Invoice For:')

        canvas_obj.drawString(405, 642, 'Invoice #:')
        canvas_obj.drawString(485, 642, self.invoice_number)
        canvas_obj.drawString(405, 630, 'Invoice Date:')
        canvas_obj.drawString(485, 630, self.invoice_date)

    def _build_story(self):
        """Gather flowable-элементы: tables by 20 samples + footer"""
        story = [] # init array
        chunks = [ #fraction all samples into 20 portion samples(matrix of samples, where row amount = total//20, column amount = 20)
            self.invoice_data[i:i + RECORDS_PER_PAGE]
            for i in range(0, len(self.invoice_data), RECORDS_PER_PAGE)
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
        columns = ['Report #', 'Project #', 'Address', 'Analysis Type', 'Qty', 'Unit Price', 'Price']
        header_row = []
        for column in columns: # we going through static array COLUMNS
            header_row.append( #add title to header
                Paragraph(column, self.styles['header'])
            )
        data = [header_row]

        for row_idx, record in enumerate(samples_chunk, start=1): # go through every sample 
            row = [] # init row   
            for key, value in record.items(): # we going through static array COLUMNS
                if key in ['unit_price', 'total']:
                    row.append(Paragraph(
                        str(fmt_money(value)).replace('\n', '<br/>'), # replace tag to special tab
                        self.styles['cell'], #attach style for cell 
                    ))
                else:
                    row.append(Paragraph(
                        str(value).replace('\n', '<br/>'), # replace tag to special tab
                        self.styles['cell'], #attach style for cell 
                    ))

            data.append(row) # append row

        if len(samples_chunk) < 20:
            for _ in range(20 - len(samples_chunk)):
                row = [Paragraph('', self.styles['cell'],) for i in range(6)]
                data.append(row) # append row

        COL_WIDTHS = [55, 145, 145, 60, 45, 45, 45]
        
        header_height = 0.20 * inch 
        row_heights = [header_height] + [0.25 * inch] * (len(data) - 1)
        table = Table(data, colWidths=COL_WIDTHS, rowHeights=row_heights, repeatRows=1, hAlign='LEFT') #make table

        # making base style 
        base_set_style = [ 
            ('GRID',           (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND',     (0, 0), (-1, 0),  colors.white),
            ('VALIGN',         (0, 0), (-1, 0),  'MIDDLE'),  # шапка — по нижнему краю
            ('VALIGN',         (0, 1), (-1, -1), 'MIDDLE'),  # данные — по центру
            ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING',    (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 2),
            ('TOPPADDING',     (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 2),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [None, ROW_SHADE]),
        ]

        # setting table style
        table.setStyle(TableStyle(base_set_style))

        return table

    def _build_footer_block(self):
        """Блок под последней таблицей: даты + подпись + примечания."""
        styles = getSampleStyleSheet()
        elements = [] 
        
        elements.append(Paragraph(f'Invoice Subtotal : ${self._count_total()}', ParagraphStyle(
            "Note", parent=styles["Normal"],
            fontName="Times-Roman", fontSize=14, leading=11,
            leftIndent=390,        # every line starts 20 pt in from the frame edge
            rightIndent=0,        # optional: margin on the right side too
            firstLineIndent=0,    # optional: extra indent for the first line only
            spaceBefore=6, spaceAfter=6,
        )))

        elements.append(Paragraph(f'DEBT:     ', ParagraphStyle(
                    "Note", parent=styles["Normal"],
                    fontName="Times-Roman", fontSize=14, leading=11,
                    leftIndent=390,        # every line starts 20 pt in from the frame edge
                    rightIndent=0,        # optional: margin on the right side too
                    firstLineIndent=0,    # optional: extra indent for the first line only
                    spaceBefore=6, spaceAfter=6,
                )))

        elements.append(Paragraph(f'PAID:     ', ParagraphStyle(
                    "Note", parent=styles["Normal"],
                    fontName="Times-Roman", fontSize=14, leading=11,
                    leftIndent=390,        # every line starts 20 pt in from the frame edge
                    rightIndent=0,        # optional: margin on the right side too
                    firstLineIndent=0,    # optional: extra indent for the first line only
                    spaceBefore=6, spaceAfter=6,
                )))

        elements.append(Paragraph(payment_text.replace('\n', '<br/>'), self.styles['note']))

        spaces = '&nbsp;' * 13
        elements.append(Paragraph(f'TOTAL: {spaces} ${self._count_total()}', ParagraphStyle(
                    "Note", parent=styles["Normal"],
                    fontName="Times-Roman", fontSize=14, leading=11,
                    leftIndent=390,        # every line starts 20 pt in from the frame edge
                    rightIndent=0,        # optional: margin on the right side too
                    firstLineIndent=0,    # optional: extra indent for the first line only
                    spaceBefore=6, spaceAfter=22,
                )))

        
        return elements

    def _build_styles(self):
        base = getSampleStyleSheet()
        return {
            'cell': ParagraphStyle(
                'cell', parent=base['Normal'],
                fontSize=8, leading=8, alignment=TA_CENTER, fontName='Times-Roman',
            ),
            'header': ParagraphStyle(
                'header', parent=base['Normal'],
                fontSize=7, leading=8, alignment=TA_CENTER,
                fontName='TimesNR-Bold',
            ),
            'note': ParagraphStyle(
                "Note", parent=base["Normal"],
                fontName="Times-Roman", fontSize=6, leading=11,
                leftIndent=5,        # every line starts 20 pt in from the frame edge
                rightIndent=0,        # optional: margin on the right side too
                firstLineIndent=0,    # optional: extra indent for the first line only
                spaceBefore=6, spaceAfter=6,
            ),
            'signature': ParagraphStyle(
                'signature', parent=base['Normal'],
                fontName='TimesNR-Bold', fontSize=9, leading=11,
                alignment=TA_LEFT,
                leftIndent=6.5 * inch,    # ← вот эта ручка
            )
        }

