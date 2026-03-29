"""
Генерация PDF-квитанции расчёта маркиз на основе ReportLab.
"""

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Цвета бренда
DARK = colors.HexColor("#1a2744")
ORANGE = colors.HexColor("#e8622a")
LIGHT = colors.HexColor("#f4f6fb")
MUTED = colors.HexColor("#6b7a99")
BORDER = colors.HexColor("#dde3f0")


def generate_pdf(result: dict[str, Any]) -> io.BytesIO:
    """
    Генерирует PDF-квитанцию по результату расчёта.

    result содержит:
      total: int
      rows: list of [str, int]
      text: str
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Расчёт маркизы",
        author="Pergolamarket",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=DARK,
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica",
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
        textColor=MUTED,
    )
    total_label_style = ParagraphStyle(
        "TotalLabel",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=DARK,
    )
    total_value_style = ParagraphStyle(
        "TotalValue",
        parent=styles["Normal"],
        fontSize=14,
        fontName="Helvetica-Bold",
        textColor=ORANGE,
        alignment=TA_RIGHT,
    )
    note_style = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica",
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    )

    story = []

    # Заголовок
    story.append(Paragraph("Расчёт стоимости маркизы", title_style))
    story.append(
        Paragraph(
            f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            subtitle_style,
        )
    )

    # Таблица детализации
    rows = result.get("rows", [])
    total = result.get("total", 0)

    table_data = [
        [
            Paragraph("Позиция", label_style),
            Paragraph("Стоимость, ₽", ParagraphStyle("LR", parent=label_style, alignment=TA_RIGHT)),
        ]
    ]

    for i, row in enumerate(rows):
        label, value = row[0], row[1]
        is_last = i == len(rows) - 1
        row_label_style = ParagraphStyle(
            f"RL{i}",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold" if is_last else "Helvetica",
            textColor=DARK,
        )
        row_value_style = ParagraphStyle(
            f"RV{i}",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold" if is_last else "Helvetica",
            textColor=ORANGE if is_last else DARK,
            alignment=TA_RIGHT,
        )
        table_data.append(
            [
                Paragraph(label, row_label_style),
                Paragraph(f"{int(value):,}".replace(",", "\u00a0"), row_value_style),
            ]
        )

    col_widths = [120 * mm, 40 * mm]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

    tbl_style = TableStyle(
        [
            # Заголовок
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
            ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4 * mm),
            ("TOPPADDING", (0, 0), (-1, 0), 3 * mm),
            # Строки
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("TOPPADDING", (0, 1), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
            # Линии
            ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER),
            ("LINEBELOW", (0, 1), (-1, -2), 0.5, BORDER),
            # Итоговая строка
            ("LINEABOVE", (0, -1), (-1, -1), 1.5, DARK),
            ("BACKGROUND", (0, -1), (-1, -1), LIGHT),
        ]
    )
    tbl.setStyle(tbl_style)
    story.append(tbl)
    story.append(Spacer(1, 6 * mm))

    # Итого крупно
    total_data = [
        [
            Paragraph("ИТОГО К ОПЛАТЕ:", total_label_style),
            Paragraph(f"{int(total):,}\u00a0₽".replace(",", "\u00a0"), total_value_style),
        ]
    ]
    total_tbl = Table(total_data, colWidths=col_widths)
    total_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DARK),
                ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [DARK]),
            ]
        )
    )
    story.append(total_tbl)
    story.append(Spacer(1, 8 * mm))

    story.append(
        Paragraph(
            "Расчёт является предварительным. Точная стоимость уточняется у менеджера.",
            note_style,
        )
    )
    story.append(
        Paragraph(
            "pergolamarket.ru · zakaz@infopergola.ru",
            note_style,
        )
    )

    doc.build(story)
    buf.seek(0)
    return buf
