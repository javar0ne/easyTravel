from typing import Final

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Table, TableStyle, Paragraph


def register_font_style():
    pdfmetrics.registerFont(TTFont("Outfit-Thin", "app/static/font/Outfit-Thin.ttf"))
    pdfmetrics.registerFont(TTFont("Outfit-ExtraLight", "app/static/font/Outfit-ExtraLight.ttf"))
    pdfmetrics.registerFont(TTFont("Outfit-Light", "app/static/font/Outfit-Light.ttf"))
    pdfmetrics.registerFont(TTFont("Outfit-Regular", "app/static/font/Outfit-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Outfit-Medium", "app/static/font/Outfit-Medium.ttf"))
    pdfmetrics.registerFont(TTFont("Outfit-SemiBold", "app/static/font/Outfit-SemiBold.ttf"))
    pdfmetrics.registerFont(TTFont("Outfit-Bold", "app/static/font/Outfit-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Outfit-ExtraBold", "app/static/font/Outfit-ExtraBold.ttf"))
    pdfmetrics.registerFont(TTFont("Outfit-Black", "app/static/font/Outfit-Black.ttf"))


class PdfItinerary(Canvas):
    WIDTH_PDF, HEIGHT_PDF = A4
    MARGIN_LEFT: Final = 30
    MARGIN_RIGHT: Final = WIDTH_PDF - 30
    LIMIT_PAGE_BREAKS: Final = 250
    TABLE_STYLE: Final = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                     ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                     ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                     ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                     ('FONTNAME', (0, 0), (-1, 0), 'Outfit-SemiBold'),
                                     ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                     ('GRID', (0, 0), (-1, -1), 1, colors.dimgrey)])
    TABLE_HEADER = ['Period', 'Location', 'Description', 'Duration']
    y_offset = HEIGHT_PDF - 40

    def __init__(self, buffer):
        super().__init__(buffer,
                         pagesize=A4,
                         bottomup=1,
                         encrypt=None)
        register_font_style()

    def draw_header(self, itinerary):
        start_date = itinerary.start_date.strftime("%d/%m/%Y")
        end_date = itinerary.end_date.strftime("%d/%m/%Y")

        self.setTitle(f"Itinerario {itinerary.city} del {start_date} - {end_date}")
        self.setFont("Outfit-Bold", 18)
        self.drawString(self.MARGIN_LEFT, self.y_offset, "easyTravel")

        self.y_offset -= 40
        self.setFont("Outfit-Bold", 20, leading=True)
        number_day = len(itinerary.details)
        self.drawString(self.MARGIN_LEFT, self.y_offset, f"{ number_day } Days in { itinerary.city }")

    def draw_itinerary_information(self, itinerary):
        start_date = itinerary.start_date.strftime("%d/%m/%Y")
        end_date = itinerary.end_date.strftime("%d/%m/%Y")
        self.y_offset -= 15

        self.setFont("Outfit-Regular", 10)
        self.setFillColor(colors.lightslategrey)
        self.drawString(self.MARGIN_LEFT, self.y_offset, f"{start_date} - {end_date}")

    def draw_days_itinerary(self, itinerary):
        self.y_offset -= 40
        for day_detail in itinerary.details:
            if self.y_offset < self.LIMIT_PAGE_BREAKS:
                self.showPage()
                self.reset_y_offset()
            self.setFillColor(colors.black)
            self.rect(self.MARGIN_LEFT, self.y_offset-4, self.MARGIN_RIGHT-30, 16, fill=True, stroke=False)
            self.setFont("Outfit-SemiBold", 12)
            self.setFillColor(colors.white)
            self.drawString(self.MARGIN_LEFT+5, self.y_offset, f"Day {day_detail.day}")

            self.draw_stages_itinerary(day_detail)
            self.y_offset -= 50

    def draw_stages_itinerary(self, detail):
        self.y_offset -= 10
        self.setFont("Outfit-Regular", 10)
        data = [self.TABLE_HEADER]
        for stage in detail.stages:
            data.append([Paragraph(stage.period),
                         Paragraph(stage.title),
                         Paragraph(stage.description),
                         Paragraph(f"{stage.avg_duration}")])

        table = Table(data, colWidths=[60, 100, self.MARGIN_RIGHT - 240, 50])
        table.setStyle(self.TABLE_STYLE)
        table_width, table_height = table.wrapOn(self, self.WIDTH_PDF, self.HEIGHT_PDF)
        table.drawOn(self, self.MARGIN_LEFT, self.y_offset - table_height)
        self.y_offset -= table_height

    def reset_y_offset(self):
        self.y_offset = self.HEIGHT_PDF - 40