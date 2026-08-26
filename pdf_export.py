import os
from datetime import datetime

from fpdf import FPDF

_FONT_CANDIDATES = [
    os.getenv("PDF_FONT_PATH", ""),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


def _find_font() -> str:
    for path in _FONT_CANDIDATES:
        if path and os.path.isfile(path):
            return path
    raise FileNotFoundError(
        "Не найден TTF-шрифт с поддержкой кириллицы. "
        "Установите fonts-dejavu-core или задайте PDF_FONT_PATH."
    )


def build_pdf(text: str) -> bytes:
    font_path = _find_font()

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Body", "", font_path)
    pdf.set_font("Body", size=11)

    pdf.set_font_size(9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, datetime.now().strftime("%d.%m.%Y %H:%M"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font_size(11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, text)

    return bytes(pdf.output())
