"""
Building blocks shared by the laboratory PDF reports.

A report module (e.g. report_generator/pcm/pcm_report_generator.py) describes only what is
specific to its analysis - table columns, notes, footer details - and takes everything else
from here: lab info, font, page header, page numbers, signature. A new lab address or logo
is changed once, in this file.
"""
from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Callable
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Table, TableStyle


# ---------- Assets (stored next to the PLM report) ----------
ASSETS_DIR = Path(__file__).resolve().parent / 'plm'
LOGO_PATH = ASSETS_DIR / 'allab_logo.png'
SIGNATURE_PATH = ASSETS_DIR / 'lab_director_sign.jpg'

# only the bold face of Times New Roman is shipped, all report text except notes uses it
FONT = 'TimesNR-Bold'
NOTE_FONT = 'Helvetica'
pdfmetrics.registerFont(TTFont(FONT, str(ASSETS_DIR / 'Times New Roman_bold.ttf')))


# ---------- Laboratory ----------
LAB_INFO = {
    'name': 'ALLAB',
    'address_line1': '1544 East 13th Street',
    'address_line2': 'Brooklyn, NY 11230',
    'phone': 'Phone: (718) 864-3666',
    'elap': 'NYS-DOH ELAP # 12118',
}


# ---------- Page: letter, landscape ----------
PAGE_SIZE = landscape(letter)
LEFT_MARGIN = RIGHT_MARGIN = 0.4 * inch
TOP_MARGIN = 1.30 * inch        # room for the page header (title, lab address, 3 info rows)
BOTTOM_MARGIN = 0.4 * inch      # room for 'Page X of Y'
CONTENT_WIDTH = PAGE_SIZE[0] - LEFT_MARGIN - RIGHT_MARGIN


# ---------- Text styles ----------
STYLES = {
    'table_header': ParagraphStyle('table_header', fontName=FONT, fontSize=7, leading=8, alignment=TA_CENTER),
    'table_cell': ParagraphStyle('table_cell', fontName=FONT, fontSize=8, leading=9, alignment=TA_CENTER),
    'detail': ParagraphStyle('detail', fontName=FONT, fontSize=9, leading=11, alignment=TA_LEFT),
    'note': ParagraphStyle('note', fontName=NOTE_FONT, fontSize=6, leading=7.5, alignment=TA_LEFT),
}


def paragraph(text, style):
    """Paragraph for any text from the database: '&' or '<' would break ReportLab markup, so it is escaped."""
    return Paragraph(escape(str(text)).replace('\n', '<br/>'), STYLES[style])


# ---------- Value formatting, None gives empty text ----------
def fmt_date(value):
    return f'{value:%m/%d/%Y}' if value else ''

def fmt_time(value):
    return f'{value:%H:%M}' if value else ''

def fmt_number(value):
    """Number without trailing zeros: 2376.00 -> '2376', 9.90 -> '9.9', 0 -> '0'."""
    if value is None:
        return ''
    text = f'{Decimal(str(value)):f}'
    return text.rstrip('0').rstrip('.') if '.' in text else text

def fmt_fixed(value, places):
    """Number with a fixed count of decimals: fmt_fixed(0.01, 3) -> '0.010'."""
    if value is None:
        return ''
    return f'{Decimal(str(value)):.{places}f}'


# ---------- Samples table ----------
@dataclass(frozen=True)
class ReportColumn:
    title: str                          # '\n' splits the header into lines
    width: float                        # relative width, columns are scaled to fill the page
    value: Callable                     # sample -> cell text; None gives an empty cell
    highlight: Callable | None = None   # sample -> True paints the cell yellow

def fit_column_widths(columns, available_width=CONTENT_WIDTH):
    total = sum(column.width for column in columns)
    return [column.width * available_width / total for column in columns]

def samples_table(columns, samples):
    """One row per sample. When the table continues on the next page, the header row is repeated."""
    data = [[paragraph(column.title, 'table_header') for column in columns]]
    style = [
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.lightgrey),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 2),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 2),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]

    for row_index, sample in enumerate(samples, start=1):
        row = []
        for col_index, column in enumerate(columns):
            value = column.value(sample)
            row.append(paragraph('' if value is None else value, 'table_cell'))
            if column.highlight and column.highlight(sample):
                style.append(('BACKGROUND', (col_index, row_index), (col_index, row_index), colors.yellow))
        data.append(row)

    table = Table(data, colWidths=fit_column_widths(columns), repeatRows=1)
    table.setStyle(TableStyle(style))
    return table


# ---------- Blocks under the samples table ----------
def details_table(rows):
    """Borderless grid of 'Label: value' texts, e.g. the dates of the project."""
    column_count = max(len(row) for row in rows)
    data = [[paragraph(text, 'detail') for text in row] + [''] * (column_count - len(row)) for row in rows]
    table = Table(data, colWidths=[CONTENT_WIDTH / column_count] * column_count)
    table.setStyle(TableStyle([
        ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    return table

def signature_block():
    """'Lab Director:' and the signature image, pushed to the right edge."""
    label_width = 0.9 * inch
    image_width = 1.5 * inch
    signature = Image(str(SIGNATURE_PATH), width=image_width, height=0.5 * inch, kind='proportional')
    table = Table(
        [['', paragraph('Lab Director:', 'table_cell'), signature]],
        colWidths=[CONTENT_WIDTH - label_width - image_width, label_width, image_width],
    )
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',  (1, 0), (1, 0),   'RIGHT'),
        ('ALIGN',  (2, 0), (2, 0),   'LEFT'),
    ]))
    return table

def notes_block(notes):
    return [paragraph(text, 'note') for text in notes]


# ---------- Page header and page numbers ----------
def draw_page_header(canvas_obj, title, subtitle, client_rows, report_rows):
    """
    Header drawn on every page: logo, title, lab address, client info on the left, report info on the right.
        client_rows: [(label, value), ...]   e.g. ('Client Name:', 'ACME')
        report_rows: [text, ...]             e.g. 'Report ID: 26-0001'
    TOP_MARGIN leaves room for 3 rows on each side.
    """
    page_width, page_height = PAGE_SIZE
    right_x = page_width - RIGHT_MARGIN
    canvas_obj.saveState()

    canvas_obj.drawImage(str(LOGO_PATH), LEFT_MARGIN, page_height - 0.8 * inch,
                         width=0.8 * inch, height=0.5 * inch, preserveAspectRatio=True, mask='auto')

    canvas_obj.setFont(FONT, 14)
    canvas_obj.drawCentredString(page_width / 2, page_height - 0.45 * inch, title)
    canvas_obj.setFont(FONT, 10)
    canvas_obj.drawCentredString(page_width / 2, page_height - 0.62 * inch, subtitle)

    canvas_obj.setFont(FONT, 8)
    lab_lines = [LAB_INFO['address_line1'], LAB_INFO['address_line2'], LAB_INFO['phone']]
    for i, line in enumerate(lab_lines):
        canvas_obj.drawRightString(right_x, page_height - (0.40 + 0.12 * i) * inch, line)

    canvas_obj.setFont(FONT, 9)
    first_row_y = page_height - 0.95 * inch
    row_height = 0.15 * inch
    for i, (label, value) in enumerate(client_rows):
        y = first_row_y - i * row_height
        canvas_obj.drawString(LEFT_MARGIN, y, label)
        canvas_obj.drawString(LEFT_MARGIN + 1.3 * inch, y, str(value or ''))
    for i, text in enumerate(report_rows):
        canvas_obj.drawRightString(right_x, first_row_y - i * row_height, text)

    canvas_obj.restoreState()

class NumberedCanvas(canvas.Canvas):
    """Keeps the pages until save() to know their count, then writes 'Page X of Y' on each."""

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
            self.setFont(FONT, 9)
            self.drawCentredString(self._pagesize[0] / 2, BOTTOM_MARGIN / 2,
                                   f'Page {self._pageNumber} of {total_pages}')
            super().showPage()
        super().save()


# ---------- Document ----------
def build_pdf(story, draw_header, title):
    """Renders the story on letter landscape pages, draw_header(canvas, doc) runs on every page. Returns BytesIO."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=title,
        author=LAB_INFO['name'],
    )
    doc.build(story, onFirstPage=draw_header, onLaterPages=draw_header, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
