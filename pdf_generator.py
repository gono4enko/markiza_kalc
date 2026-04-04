"""
Генерация коммерческого предложения (КП) для маркиз.
Формат А4, две страницы, фирменный стиль Pergolamarket.
"""

import io
import os
import re
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from kp_content import get_pdf_label
from motor_commercial import (
    get_motor_commercial,
    get_sensor_commercial_detail,
    get_sensor_pdf_pair,
)

# ---------------------------------------------------------------------------
# Пути к шрифтам
# ---------------------------------------------------------------------------
_BASE = os.path.dirname(os.path.abspath(__file__))
_FONTS = os.path.join(_BASE, "static", "fonts")

_FONTS_REGISTERED = False


def _ensure_fonts() -> None:
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    pdfmetrics.registerFont(TTFont("Arial",         os.path.join(_FONTS, "Arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold",    os.path.join(_FONTS, "Arial-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Italic",  os.path.join(_FONTS, "Arial-Italic.ttf")))
    # Arial Unicode — для символа ₽ (U+20BD), которого нет в обычном Arial
    pdfmetrics.registerFont(TTFont("Arial-Unicode", os.path.join(_FONTS, "Arial-Unicode.ttf")))
    _FONTS_REGISTERED = True


# ---------------------------------------------------------------------------
# Цвета бренда
# ---------------------------------------------------------------------------
C_DARK    = colors.HexColor("#1a2744")   # тёмно-синий фон
C_ACCENT  = colors.HexColor("#e8622a")   # оранжевый акцент
C_LIGHT   = colors.HexColor("#f4f6fb")   # светло-серый фон секций
C_MID     = colors.HexColor("#6b7a99")   # вторичный текст
C_BORDER  = colors.HexColor("#dde3f0")   # разделители
C_WHITE   = colors.white
C_ORANGE2 = colors.HexColor("#d4521e")   # тёмный акцент для hover-таблицы

PAGE_W, PAGE_H = A4                       # 210 × 297 мм

# ---------------------------------------------------------------------------
# Константы компании
# ---------------------------------------------------------------------------
COMPANY_NAME    = "Pergolamarket"
COMPANY_SITE    = "pergolamarket.ru"
COMPANY_EMAIL   = "zakaz@infopergola.ru"
COMPANY_PHONE   = "+7 (906) 429-74-20"

# ---------------------------------------------------------------------------
# Хелперы форматирования
# ---------------------------------------------------------------------------

def _fmt(value: int | float) -> str:
    """Форматирует число как '145\u00a0605\u00a0руб.' для PDF."""
    return f"{int(value):,}".replace(",", "\u00a0") + "\u00a0руб."


def _fmt_plain(value: int | float) -> str:
    """Форматирует число без знака валюты."""
    return f"{int(value):,}".replace(",", "\u00a0")


# ---------------------------------------------------------------------------
# Декоративные функции для Canvas (рисуются поверх platypus)
# ---------------------------------------------------------------------------

class _KPDoc(BaseDocTemplate):
    """Документ с кастомными шапкой / подвалом на каждой странице."""

    def __init__(self, buf: io.BytesIO, title: str, kp_number: str, date_str: str):
        _ensure_fonts()
        super().__init__(
            buf,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=45 * mm,   # место для шапки
            bottomMargin=22 * mm,
            title=title,
            author=COMPANY_NAME,
        )
        self.kp_number = kp_number
        self.date_str  = date_str
        self._build_templates()

    def _build_templates(self) -> None:
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            PAGE_W - self.leftMargin - self.rightMargin,
            PAGE_H - self.topMargin - self.bottomMargin,
            id="main",
        )
        self.addPageTemplates([
            PageTemplate(id="standard", frames=[frame], onPage=self._draw_page),
        ])

    def _draw_page(self, c: canvas.Canvas, doc: "BaseDocTemplate") -> None:
        c.saveState()

        # ── Шапка: тёмный баннер ──────────────────────────────────────────
        banner_h = 36 * mm
        c.setFillColor(C_DARK)
        c.rect(0, PAGE_H - banner_h, PAGE_W, banner_h, fill=1, stroke=0)

        # Оранжевая полоса снизу шапки
        c.setFillColor(C_ACCENT)
        c.rect(0, PAGE_H - banner_h - 2 * mm, PAGE_W, 2 * mm, fill=1, stroke=0)

        # Логотип / название
        c.setFillColor(C_WHITE)
        c.setFont("Arial-Bold", 20)
        c.drawString(18 * mm, PAGE_H - 22 * mm, COMPANY_NAME)

        # Слоган
        c.setFont("Arial", 9)
        c.setFillColor(colors.HexColor("#9aaabf"))
        c.drawString(18 * mm, PAGE_H - 30 * mm, "Маркизы, навесы и солнцезащитные системы")

        # Номер КП и дата — правый блок шапки
        c.setFillColor(C_WHITE)
        c.setFont("Arial-Bold", 9)
        kp_x = PAGE_W - 18 * mm
        c.drawRightString(kp_x, PAGE_H - 18 * mm, f"КП № {doc.kp_number}")
        c.setFont("Arial", 9)
        c.setFillColor(colors.HexColor("#9aaabf"))
        c.drawRightString(kp_x, PAGE_H - 25 * mm, f"Дата: {doc.date_str}")
        c.drawRightString(kp_x, PAGE_H - 31 * mm, COMPANY_SITE)

        # ── Подвал ────────────────────────────────────────────────────────
        footer_y = 14 * mm
        c.setFillColor(C_DARK)
        c.rect(0, 0, PAGE_W, footer_y, fill=1, stroke=0)

        c.setFillColor(C_WHITE)
        c.setFont("Arial", 7.5)
        c.drawString(18 * mm, 9 * mm, f"{COMPANY_SITE}  ·  {COMPANY_EMAIL}  ·  {COMPANY_PHONE}")
        c.setFont("Arial", 7)
        c.setFillColor(colors.HexColor("#9aaabf"))
        c.drawString(18 * mm, 5 * mm, "Расчёт является предварительным. Точная стоимость уточняется у менеджера.")

        # Номер страницы
        c.setFillColor(C_WHITE)
        c.setFont("Arial", 8)
        c.drawRightString(PAGE_W - 18 * mm, 7 * mm, f"Стр. {doc.page}")

        c.restoreState()


# ---------------------------------------------------------------------------
# Стили параграфов
# ---------------------------------------------------------------------------

def _styles() -> dict[str, ParagraphStyle]:
    def ps(name: str, **kwargs) -> ParagraphStyle:
        return ParagraphStyle(name, **kwargs)

    return {
        "h1": ps("h1",
            fontName="Arial-Bold", fontSize=18, textColor=C_DARK,
            spaceAfter=3 * mm),
        "h2": ps("h2",
            fontName="Arial-Bold", fontSize=12, textColor=C_DARK,
            spaceAfter=2 * mm, spaceBefore=4 * mm),
        "label": ps("label",
            fontName="Arial", fontSize=8, textColor=C_MID,
            spaceAfter=0.5 * mm),
        "value": ps("value",
            fontName="Arial-Bold", fontSize=10, textColor=C_DARK,
            spaceAfter=1.5 * mm),
        "body": ps("body",
            fontName="Arial", fontSize=9.5, textColor=C_DARK,
            spaceAfter=1.5 * mm, leading=13),
        "small": ps("small",
            fontName="Arial-Italic", fontSize=8, textColor=C_MID,
            spaceAfter=1.5 * mm, leading=11),
        "tbl_header": ps("tbl_header",
            fontName="Arial-Bold", fontSize=8.5, textColor=C_WHITE),
        "tbl_header_r": ps("tbl_header_r",
            fontName="Arial-Bold", fontSize=8.5, textColor=C_WHITE,
            alignment=TA_RIGHT),
        "tbl_row": ps("tbl_row",
            fontName="Arial", fontSize=9.5, textColor=C_DARK, leading=13),
        "tbl_row_r": ps("tbl_row_r",
            fontName="Arial", fontSize=9.5, textColor=C_DARK,
            alignment=TA_RIGHT, leading=13),
        "tbl_zero": ps("tbl_zero",
            fontName="Arial-Italic", fontSize=9, textColor=C_MID,
            alignment=TA_RIGHT),
        "total_label": ps("total_label",
            fontName="Arial-Bold", fontSize=13, textColor=C_WHITE),
        "total_value": ps("total_value",
            fontName="Arial-Bold", fontSize=13, textColor=C_ACCENT,
            alignment=TA_RIGHT),
        "note": ps("note",
            fontName="Arial-Italic", fontSize=8, textColor=C_MID,
            alignment=TA_CENTER, leading=11),
        "term_bullet": ps("term_bullet",
            fontName="Arial", fontSize=8.5, textColor=C_DARK,
            leading=13, leftIndent=4 * mm),
    }


# ---------------------------------------------------------------------------
# Вспомогательные блоки
# ---------------------------------------------------------------------------

def _kv_table(pairs: list[tuple[str, str]], s: dict) -> Table:
    """Сетка ключ-значение в 2 или 4 колонки."""
    col_w = (PAGE_W - 36 * mm) / 2
    data = []
    row: list = []
    for i, (k, v) in enumerate(pairs):
        row.append(Paragraph(k, s["label"]))
        row.append(Paragraph(v, s["value"]))
        if len(row) == 4 or i == len(pairs) - 1:
            if len(row) < 4:
                row += ["", ""]
            data.append(row)
            row = []
    tbl = Table(data, colWidths=[col_w * 0.38, col_w * 0.62, col_w * 0.38, col_w * 0.62])
    tbl.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 1.5 * mm),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 1 * mm),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
        ("LINEBELOW",    (0, 0), (-1, -2), 0.5, C_BORDER),
    ]))
    return tbl


def _section_header(text: str, s: dict) -> Table:
    """Цветная полоска-заголовок секции."""
    tbl = Table([[Paragraph(text, s["h2"])]],
                colWidths=[PAGE_W - 36 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), C_LIGHT),
        ("LEFTPADDING",  (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING",   (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2.5 * mm),
        ("LINEBELOW",    (0, 0), (-1, -1), 1.5, C_ACCENT),
    ]))
    return tbl


# Ключевые преимущества ткани Sattler SUN-TEX (локтевые / витринные маркизы)
_SATTLER_ADV_INTRO = (
    "Ткань — это то, на что вы смотрите каждый день и что первым принимает удары солнца, "
    "дождя и ветра. В расчёте используется <b>Sattler SUN-TEX</b> (Австрия, более 100 лет "
    "на рынке, поставки в 60+ стран мира). Простыми словами — почему это важно:"
)
_SATTLER_ADV_BULLETS: tuple[str, ...] = (
    "<b>Цвет не выгорает даже через 7 лет</b> под прямым солнцем. "
    "Краситель вводится в волокно до прядения (технология solution-dyed акрил) — "
    "он внутри каждой нити, а не на поверхности. Принципиальное отличие от дешёвых аналогов.",

    "<b>Защищает от ультрафиолета</b> как солнцезащитный крем с SPF 40–80. "
    "Под тенью маркизы Sattler дети и гости в безопасности даже в полдень "
    "(испытания по стандарту UV 801).",

    "<b>Грязь и дождь скатываются сами</b> — отделка TEXgard без вредной химии PFAS. "
    "Уход: промыть тёплой водой раз в сезон. Сертификат OEKO-TEX: "
    "безопасно для детей и домашних животных.",

    "<b>Коллекция Lumera и Lumera 3D</b> — насыщенные цвета и «сияющая» поверхность "
    "за счёт особого волокна CBA. Смотрится дороже, выглядит свежо даже после нескольких сезонов.",

    "<b>Lumera All Weather</b> — усиленная защита от намокания при сохранении мягкости. "
    "Оптимально для регионов с частыми дождями.",

    "<b>Elements Cross Fiber</b> — ткань из переработанного сырья. "
    "Качество и внешний вид такие же, как у стандартных серий.",
)


def _append_sattler_fabric_advantages(story: list, s: dict[str, ParagraphStyle]) -> None:
    """Добавляет в story секцию преимуществ SUN-TEX для локтевых и витринных маркиз."""
    story.append(Spacer(1, 3 * mm))
    story.append(_section_header("ТКАНЬ SATTLER SUN-TEX — КЛЮЧЕВЫЕ ПРЕИМУЩЕСТВА", s))
    story.append(Spacer(1, 2 * mm))
    intro_style = ParagraphStyle(
        "sattler_adv_intro",
        parent=s["body"],
        spaceAfter=2 * mm,
    )
    story.append(Paragraph(_SATTLER_ADV_INTRO, intro_style))
    for line in _SATTLER_ADV_BULLETS:
        story.append(Paragraph(f"• {line}", s["term_bullet"]))
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph(
        "Подробнее: <font color='#e8622a'>suntex.sattler.com</font> (разделы Quality ELEMENTS, Lumera, Cross Fiber, World of Sattler).",
        ParagraphStyle(
            "sattler_adv_note",
            fontName="Arial-Italic",
            fontSize=8,
            textColor=C_MID,
            leading=11,
            spaceAfter=0,
        ),
    ))


def _append_selected_equipment_section(
    story: list,
    s: dict[str, ParagraphStyle],
    params: dict[str, Any],
    content_w: float,
) -> None:
    """
    Автоматика и датчик: принцип работы, функционал — после эскиза, перед контактами.
    """
    if str(params.get("control", "") or "").lower() != "electric":
        return

    awning_t = params.get("awning_type", "")
    if awning_t == "zip":
        mb = str(params.get("motor_brand", "simu") or "simu")
    else:
        mb = str(params.get("motor_brand", "decolife") or "decolife")

    mc = get_motor_commercial(mb)
    story.append(Spacer(1, 4 * mm))
    story.append(_section_header(
        get_pdf_label("section_equipment", "ПОДОБРАННАЯ АВТОМАТИКА И УПРАВЛЕНИЕ"),
        s,
    ))
    story.append(Spacer(1, 2 * mm))

    head_style = ParagraphStyle(
        "equip_motor_head",
        parent=s["body"],
        fontName="Arial-Bold",
        fontSize=10,
        textColor=C_DARK,
        spaceAfter=2 * mm,
    )
    story.append(Paragraph(f"Электропривод <b>{mc['display_name']}</b>", head_style))
    story.append(Paragraph(mc["headline"], ParagraphStyle(
        "equip_motor_sub",
        parent=s["body"],
        fontName="Arial-Bold",
        fontSize=9.5,
        textColor=C_MID,
        spaceAfter=2 * mm,
    )))
    story.append(Paragraph(mc["principle_html"], s["body"]))
    story.append(Spacer(1, 1 * mm))
    for line in mc["bullets_html"]:
        story.append(Paragraph(f"• {line}", s["term_bullet"]))

    kit = str(mc.get("image_kit") or "").strip()
    if kit:
        pth = _static_url_to_fs(kit)
        if pth:
            story.append(Spacer(1, 2 * mm))
            img_w = min(content_w - 8 * mm, 100 * mm)
            story.append(_image_card(pth, "Привод, пульт и комплект автоматики", max_w=img_w, s=s, max_h=55 * mm))

    sensor = str(params.get("sensor_type", "none") or "none")
    if awning_t != "zip" and sensor in ("radio", "speed"):
        sd = get_sensor_commercial_detail(mb, sensor)
        if sd:
            story.append(Spacer(1, 3 * mm))
            story.append(_section_header(
                get_pdf_label("section_sensor", "ДАТЧИК — ЗАЩИТА И КОМФОРТ"),
                s,
            ))
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(
                f"<b>Модель в предложении:</b> {sd['model']}",
                ParagraphStyle(
                    "sensor_model",
                    parent=s["body"],
                    fontName="Arial-Bold",
                    spaceAfter=2 * mm,
                ),
            ))
            story.append(Paragraph(sd["intro"], s["body"]))
            story.append(Spacer(1, 1 * mm))
            for line in sd["bullets_html"]:
                story.append(Paragraph(f"• {line}", s["term_bullet"]))
            simg = str(sd.get("image") or "").strip()
            if simg:
                spth = _static_url_to_fs(simg)
                if spth:
                    story.append(Spacer(1, 2 * mm))
                    img_w = min(content_w - 8 * mm, 90 * mm)
                    story.append(_image_card(spth, sd["model"], max_w=img_w, s=s, max_h=50 * mm))

    # LED в локтях — локтевая маркиза, опция «С LED подсветкой»
    lo = str(params.get("lighting_option", "none") or "none")
    if awning_t == "standard" and lo == "standard":
        story.append(Spacer(1, 3 * mm))
        story.append(_section_header(
            get_pdf_label("section_led", "LED-ПОДСВЕТКА В ЛОКТЯХ (CONCEPT LED)"),
            s,
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            "<b>Вечерний свет без отдельных светильников:</b> в профиль складных локтей серии "
            "<b>Concept LED</b> встроена линейная LED-лента. Тёплый рассеянный свет под козырьком "
            "подчёркивает зону отдыха; днём подсветка визуально не перегружает конструкцию.",
            s["body"],
        ))
        story.append(Spacer(1, 1 * mm))
        for line in (
            "LED размещается в <b>канале локтя</b> — без навесных светильников на фасаде.",
            "Управление согласуется с комплектом автоматики: отдельный канал на пульте или сценарии при настройке (уточняется при монтаже).",
            "Совместимость с сериями <b>Concept / Concept LED</b> в рамках подобранной под ваш вылет конфигурации Gaviota.",
        ):
            story.append(Paragraph(f"• {line}", s["term_bullet"]))
        p_arm = _static_url_to_fs("/static/img/led_concept_arm_detail.png")
        p_ter = _static_url_to_fs("/static/img/led_concept_terrace.png")
        if p_arm and p_ter:
            gap = 4 * mm
            col_w = (content_w - gap) / 2
            (dw_l, dh), (dw_r, _dh_r) = _led_image_pair_equal_height(
                p_arm, p_ter, col_w, 52 * mm,
            )
            c1 = _image_card(
                p_arm,
                "Крупно: LED-лента в канале локтя",
                max_w=col_w,
                s=s,
                max_h=52 * mm,
                fixed_draw_w=dw_l,
                fixed_draw_h=dh,
            )
            c2 = _image_card(
                p_ter,
                "Терраса с подсветкой Concept LED",
                max_w=col_w,
                s=s,
                max_h=52 * mm,
                fixed_draw_w=dw_r,
                fixed_draw_h=dh,
            )
            row_led = Table([[c1, c2]], colWidths=[col_w, col_w])
            row_led.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(Spacer(1, 2 * mm))
            story.append(row_led)
        elif p_arm:
            story.append(Spacer(1, 2 * mm))
            img_w = min(content_w - 8 * mm, 95 * mm)
            story.append(_image_card(p_arm, "LED-лента в локте маркизы", max_w=img_w, s=s, max_h=50 * mm))
        elif p_ter:
            story.append(Spacer(1, 2 * mm))
            img_w = min(content_w - 8 * mm, 95 * mm)
            story.append(_image_card(p_ter, "Терраса с подсветкой Concept LED", max_w=img_w, s=s, max_h=50 * mm))


def _append_elbow_arms_section(story: list, s: dict[str, ParagraphStyle], content_w: float) -> None:
    """Секция про тип локтей, сечение и натяжение — только для локтевой маркизы."""
    story.append(Spacer(1, 3 * mm))
    story.append(_section_header("ЛОКТИ И НАТЯЖЕНИЕ ПОЛОТНА", s))
    story.append(Spacer(1, 2 * mm))

    ps_body = ParagraphStyle("elbow_body", parent=s["body"], spaceAfter=2 * mm)
    story.append(Paragraph(
        "<b>Как мы выбираем локти под ваш заказ:</b> складные плечи (локти) — это то, "
        "что держит полотно в открытом состоянии и противостоит ветру. "
        "Чем больше вылет, тем мощнее должны быть локти. "
        "<b>Мы уже выбрали правильную серию под ваши размеры</b> — она указана выше. "
        "Таблица ниже поясняет разницу между сериями, если интересно:",
        ps_body,
    ))
    story.append(Paragraph(
        "Группа <b>Gaviota</b> (Испания) в линейке «невидимых» плеч <b>M1</b> предлагает классы <b>Smart</b> (компактный профиль), "
        "<b>Premium / Premium Plus</b> (усиленные плечи с внутренним натяжением), <b>Concept</b> — в т.ч. со встроенной LED-лентой, "
        "<b>Arko</b> — для больших вылетов, с текстильным натяжением в конструкции плеча. Каталог: "
        "<a href=\"https://www.gaviotagroup.com/categoria-producto/toldo-y-proteccion-solar/\" color=\"#2563eb\">"
        "gaviotagroup.com — toldos y protección solar</a>.",
        ps_body,
    ))
    story.append(Paragraph(
        "<b>Принцип натяжения:</b> в современных локтях усилие на полотно задают пружины и/или цепь внутри профиля "
        "(в отдельных сериях — текстильная лента). При раскрытии полотно натягивается без ручной подтяжки после каждого цикла. "
        "Итоговую серию локтей фиксируем в проекте под ваши ширину и вылет.",
        ps_body,
    ))

    arm_cell = ParagraphStyle("arm_cell", fontName="Arial", fontSize=8, textColor=C_DARK, leading=10)
    arm_head = ParagraphStyle("arm_head", fontName="Arial-Bold", fontSize=8, textColor=C_DARK, leading=10)
    arm_rows: list[list] = [
        [
            Paragraph("Серия (тип локтя)", arm_head),
            Paragraph("Сечение профиля, мм", arm_head),
            Paragraph("Типичный макс. вылет*", arm_head),
        ],
        [
            Paragraph("Smart", arm_cell),
            Paragraph("≈ 60 × 54 (до ~65 у шарнира)", arm_cell),
            Paragraph("до 3,0 м", arm_cell),
        ],
        [
            Paragraph("Premium plus", arm_cell),
            Paragraph("≈ 80 × 82", arm_cell),
            Paragraph("до 3,5 м", arm_cell),
        ],
        [
            Paragraph("LED Concept", arm_cell),
            Paragraph("≈ 80 × 82, LED в комплекте", arm_cell),
            Paragraph("до 4,0 м", arm_cell),
        ],
        [
            Paragraph("Arko", arm_cell),
            Paragraph("≈ 76 × 95", arm_cell),
            Paragraph("до 4,0 м", arm_cell),
        ],
    ]
    w1, w2, w3 = content_w * 0.30, content_w * 0.38, content_w * 0.32
    arm_tbl = Table(arm_rows, colWidths=[w1, w2, w3])
    arm_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(arm_tbl)
    story.append(Paragraph(
        "* При вылете до 3,0 м серия Smart — оптимальный баланс цены и надёжности. "
        "При вылете от 3,5 м автоматически переходим на Premium Plus без пересчёта КП.",
        ParagraphStyle("elbow_tip", parent=s["small"],
            spaceBefore=2 * mm, spaceAfter=0,
            textColor=C_MID, fontName="Arial-Italic", fontSize=8.5),
    ))
    story.append(Paragraph(
        "* Ориентир по каталогам комплектующих; фактический предел зависит от ширины, крепления и условий эксплуатации.",
        ParagraphStyle("elbow_foot", parent=s["small"], spaceBefore=1.5 * mm, spaceAfter=0),
    ))


def _append_storefront_arms_section(
    story: list,
    s: dict[str, ParagraphStyle],
    params: dict[str, Any],
    content_w: float,
) -> None:
    """Витринная маркиза: выпадающие локти, углы, сравнение G400 / G450."""
    story.append(Spacer(1, 3 * mm))
    story.append(_section_header("КАК РАБОТАЮТ ЛОКТИ ВИТРИННОЙ МАРКИЗЫ", s))
    story.append(Spacer(1, 2 * mm))

    ps_body = ParagraphStyle("sf_body", parent=s["body"], spaceAfter=2 * mm)
    ps_bold = ParagraphStyle("sf_bold", parent=s["body"],
        fontName="Arial-Bold", spaceAfter=2 * mm)

    config = str(params.get("config", "") or "").lower()
    tilt_on = params.get("storefront_tilt_170") in (True, "true", 1, "1", "yes", "on")

    story.append(Paragraph(
        "В отличие от локтевых маркиз, где плечи раскрываются горизонтально над террасой, "
        "витринные маркизы используют <b>выпадающие подпружиненные локти</b>: "
        "они опускаются вниз и натягивают полотно перед окном или витриной.",
        ps_body,
    ))
    story.append(Paragraph(
        "<b>Почему это важно для магазина или кафе:</b>",
        ps_bold,
    ))
    story.append(Paragraph(
        "Прямые солнечные лучи создают блики на витринном стекле — "
        "товары не видны снаружи, покупатели проходят мимо. "
        "Маркиза блокирует прямое солнце: стекло становится прозрачным, "
        "товары снова видны, витрина работает на продажи. "
        "Дополнительно: температура воздуха внутри снижается — "
        "меньше затраты на кондиционирование.",
        ps_body,
    ))

    arm_cell = ParagraphStyle("sf_arm_cell", fontName="Arial",
        fontSize=8.5, textColor=C_DARK, leading=12)
    arm_head = ParagraphStyle("sf_arm_head", fontName="Arial-Bold",
        fontSize=8.5, textColor=C_DARK, leading=12)

    tilt_rows = [
        [
            Paragraph("Угол наклона", arm_head),
            Paragraph("Описание", arm_head),
            Paragraph("Когда применять", arm_head),
        ],
        [
            Paragraph("90° — стандарт", arm_cell),
            Paragraph("Козырёк горизонтально над окном", arm_cell),
            Paragraph("Защита от верхнего солнца, тень на витрине", arm_cell),
        ],
        [
            Paragraph("170° — опция (+15%)", arm_cell),
            Paragraph("Локти почти вертикально, полотно закрывает окно", arm_cell),
            Paragraph(
                "Полная защита в любое время дня. "
                "Товары, оборудование или интерьер под максимальной защитой.",
                arm_cell,
            ),
        ],
    ]

    w1, w2, w3 = content_w * 0.22, content_w * 0.38, content_w * 0.40
    tilt_style = [
        ("BACKGROUND",    (0, 0), (-1, 0), C_LIGHT),
        ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]
    if tilt_on:
        tilt_style.extend([
            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#fff3ee")),
            ("LINEABOVE",  (0, 2), (-1, 2), 1.5, C_ACCENT),
        ])
    tilt_tbl = Table(tilt_rows, colWidths=[w1, w2, w3])
    tilt_tbl.setStyle(TableStyle(tilt_style))
    story.append(tilt_tbl)

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "<b>Модели в линейке витринных маркиз Gaviota:</b>",
        ps_bold,
    ))

    st_name_g400 = ParagraphStyle(
        "sf_nm_g400",
        parent=arm_cell,
        fontName="Arial-Bold" if config == "g400" else "Arial",
        textColor=C_ACCENT if config == "g400" else C_DARK,
    )
    st_name_g450 = ParagraphStyle(
        "sf_nm_g450",
        parent=arm_cell,
        fontName="Arial-Bold" if config == "g450" else "Arial",
        textColor=C_ACCENT if config == "g450" else C_DARK,
    )
    model_rows = [
        [
            Paragraph("Модель", arm_head),
            Paragraph("Конструкция", arm_head),
            Paragraph("Ширина", arm_head),
            Paragraph("Макс. вынос", arm_head),
        ],
        [
            Paragraph(
                "G400 Italy" + (" ← выбрана" if config == "g400" else ""),
                st_name_g400,
            ),
            Paragraph("Открытая, выпадающие локти на пружинах", arm_cell),
            Paragraph("до 7 м", arm_cell),
            Paragraph("до 1,4 м", arm_cell),
        ],
        [
            Paragraph(
                "G450 Desert" + (" ← выбрана" if config == "g450" else ""),
                st_name_g450,
            ),
            Paragraph("Кассетная, полотно убирается в короб", arm_cell),
            Paragraph("до 5 м", arm_cell),
            Paragraph("до 1,0 м", arm_cell),
        ],
    ]

    wm1, wm2, wm3, wm4 = content_w * 0.22, content_w * 0.40, content_w * 0.19, content_w * 0.19
    model_style = [
        ("BACKGROUND",    (0, 0), (-1, 0), C_LIGHT),
        ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]
    if config == "g400":
        model_style.append(("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fff3ee")))
    elif config == "g450":
        model_style.append(("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#fff3ee")))
    model_tbl = Table(model_rows, colWidths=[wm1, wm2, wm3, wm4])
    model_tbl.setStyle(TableStyle(model_style))
    story.append(model_tbl)
    story.append(Paragraph(
        "* Локти Italy (пара) входят в стоимость маркизы. "
        "При вылете 0,7–1,4 м пружинный механизм обеспечивает равномерное натяжение "
        "без ручной регулировки после каждого цикла.",
        ParagraphStyle("sf_foot", parent=s["small"], spaceBefore=1.5 * mm, spaceAfter=0),
    ))


# ---------------------------------------------------------------------------
# Поиск изображений для PDF
# ---------------------------------------------------------------------------

# Карта: (awning_type, config) → имя файла схемы в static/img/
_SCHEME_FILES = {
    ("zip", "zip100"):   "zip100_scheme.png",
    ("zip", "zip130"):   "zip130_scheme.png",
    ("standard", "open"):     "standard_awning.png",
    ("standard", "semi"):     "standard_awning.png",
    ("standard", "cassette"): "standard_awning.png",
    ("storefront", "g400"):   "storefront_awning.png",
    ("storefront", "g450"):   "g450_desert.png",
}

# Карта: fabric_zip → подпапка коллекции по умолчанию
_FABRIC_ZIP_DEFAULT_FOLDER = {
    "veozip": "veozip",
}


def _get_scheme_image(params: dict[str, Any]) -> str | None:
    """Возвращает абсолютный путь к схеме конструкции или None."""
    key = (params.get("awning_type", ""), params.get("config", ""))
    fname = _SCHEME_FILES.get(key)
    if not fname:
        return None
    path = os.path.join(_BASE, "static", "img", fname)
    return path if os.path.exists(path) else None


def _static_url_to_fs(web_path: str) -> str | None:
    """Путь вида /static/img/... → абсолютный путь к файлу на диске."""
    if not web_path or not isinstance(web_path, str):
        return None
    p = web_path.strip()
    if not p.startswith("/static/"):
        return None
    rel = p[len("/static/") :].lstrip("/")
    full = os.path.join(_BASE, "static", rel)
    return full if os.path.isfile(full) else None


def _fabric_article_fs_safe(label: str) -> str:
    """Имя файла как в scripts/sync_fabric_std_thumbs.py."""
    s = (label or "").strip()
    s = re.sub(r"[^\w.\-]+", "_", s)
    return (s[:180] or "unknown")


def _suntex_thumb_local_path(params: dict[str, Any]) -> str | None:
    """Локальная миниатюра SUN-TEX: static/img/fabrics/suntex_thumbs/{fabric}/{артикул}.webp."""
    fb = str(params.get("fabric", "") or "").strip()
    art = (params.get("fabric_color_label") or params.get("fabric_swatch_label") or "").strip()
    if not fb or not art:
        return None
    safe = _fabric_article_fs_safe(art)
    base = os.path.join(_BASE, "static", "img", "fabrics", "suntex_thumbs", fb)
    for ext in (".webp", ".jpg", ".jpeg", ".png"):
        p = os.path.join(base, safe + ext)
        if os.path.isfile(p):
            return p
    return None


def _get_fabric_image(params: dict[str, Any]) -> str | io.BytesIO | None:
    """Возвращает абсолютный путь к thumb-изображению ткани или None."""
    fabrics_root = os.path.join(_BASE, "static", "img", "fabrics")
    awning_type  = params.get("awning_type", "")

    if awning_type == "zip":
        fz = params.get("fabric_zip", "veozip")

        if fz == "veozip":
            article = params.get("veozip_color", "")
            folder  = os.path.join(fabrics_root, "veozip", "thumbs")
            if article:
                path = os.path.join(folder, f"{article}.jpg")
                if os.path.exists(path):
                    return path
            # Первый доступный файл
            return _first_file(folder)

        if fz == "soltis":
            col = params.get("soltis_collection", "soltis86")
            article = params.get("soltis_color", "")
            folder = os.path.join(fabrics_root, col, "thumbs")
            if article:
                path = os.path.join(folder, f"{article}.jpg")
                if os.path.exists(path):
                    return path
            return _first_file(folder)

        if fz == "copaco":
            col = params.get("copaco_collection", "copacoSerge5")
            article = params.get("copaco_color", "")
            folder = os.path.join(fabrics_root, col, "thumbs")
            if article:
                path = os.path.join(folder, f"{article}.jpg")
                if os.path.exists(path):
                    return path
            return _first_file(folder)

    # Локтевая / витринная: только файлы приложения (см. scripts/sync_fabric_std_thumbs.py)
    if awning_type in ("standard", "storefront"):
        loc_st = _suntex_thumb_local_path(params)
        if loc_st:
            return loc_st
        raw = (params.get("fabric_swatch_url") or "").strip()
        if raw.startswith("/static/"):
            loc = _static_url_to_fs(raw)
            if loc:
                return loc

    return None


def _first_file(folder: str) -> str | None:
    """Возвращает первый .jpg файл в папке или None."""
    if not os.path.isdir(folder):
        return None
    for f in sorted(os.listdir(folder)):
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            return os.path.join(folder, f)
    return None


def _fit_image_draw_size(
    native_w: int,
    native_h: int,
    max_w: float,
    max_h: float,
) -> tuple[float, float]:
    """Вписать пропорции в прямоугольник max_w × max_h, вернуть (draw_w, draw_h)."""
    ratio = native_w / native_h
    if ratio >= max_w / max_h:
        return max_w, max_w / ratio
    return max_h * ratio, max_h


def _led_image_pair_equal_height(
    path_left: str,
    path_right: str,
    col_w: float,
    max_h: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Два кадра в колонках одинаковой номинальной ширины: одинаковая высота рисунка
    (как более «низкий» из вариантов вписывания в col_w×max_h), ширины могут различаться.
    """
    from PIL import Image as PILImage

    with PILImage.open(path_left) as pil:
        nw_l, nh_l = pil.size
    with PILImage.open(path_right) as pil:
        nw_r, nh_r = pil.size
    r_l = nw_l / nh_l
    r_r = nw_r / nh_r
    w_l, h_l = _fit_image_draw_size(nw_l, nh_l, col_w, max_h)
    w_r, h_r = _fit_image_draw_size(nw_r, nh_r, col_w, max_h)
    target_h = min(h_l, h_r)
    d_w_l = target_h * r_l
    d_w_r = target_h * r_r
    if d_w_l > col_w or d_w_r > col_w:
        scale = min(col_w / max(d_w_l, 1e-9), col_w / max(d_w_r, 1e-9), 1.0)
        target_h *= scale
        d_w_l = target_h * r_l
        d_w_r = target_h * r_r
    return (d_w_l, target_h), (d_w_r, target_h)


def _image_card(
    img_source: str | io.BytesIO,
    caption: str,
    max_w: float,
    s: dict,
    max_h: float | None = None,
    *,
    fixed_draw_w: float | None = None,
    fixed_draw_h: float | None = None,
) -> Table:
    """Возвращает ячейку-блок с изображением (пропорции сохранены) и подписью."""
    if max_h is None:
        max_h = max_w
    caption_xml = escape(caption)
    try:
        # Читаем реальные размеры через Pillow чтобы сохранить пропорции
        from PIL import Image as PILImage

        if isinstance(img_source, str):
            pil_open = PILImage.open(img_source)
        else:
            img_source.seek(0)
            pil_open = PILImage.open(img_source)
        with pil_open as pil:
            native_w, native_h = pil.size

        if fixed_draw_w is not None and fixed_draw_h is not None:
            draw_w, draw_h = fixed_draw_w, fixed_draw_h
        else:
            ratio = native_w / native_h
            # Вписываем в прямоугольник max_w × max_h
            if ratio >= max_w / max_h:
                draw_w = max_w
                draw_h = max_w / ratio
            else:
                draw_h = max_h
                draw_w = max_h * ratio

        if isinstance(img_source, str):
            img = Image(img_source, width=draw_w, height=draw_h)
        else:
            img_source.seek(0)
            img = Image(ImageReader(img_source), width=draw_w, height=draw_h)
        img.hAlign = "CENTER"
    except Exception:
        return Table([[Paragraph(caption_xml, s["small"])]])
    
    card_w = max_w  # ячейка всегда одной ширины для выравнивания

    caption_p = Paragraph(caption_xml, ParagraphStyle(
        "img_cap",
        fontName="Arial",
        fontSize=8.5,
        textColor=C_DARK,
        alignment=TA_CENTER,
        spaceAfter=0,
    ))

    tbl = Table(
        [[img], [caption_p]],
        colWidths=[card_w],
    )
    tbl.setStyle(TableStyle([
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, 0),  1.5 * mm),
        ("BOTTOMPADDING",(0, 1), (-1, 1),  0),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOX",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.white),
        ("BACKGROUND",   (0, 1), (-1, 1),  C_LIGHT),
    ]))
    return tbl


def _append_benefits_block(
    story: list,
    s: dict,
    params: dict,
    content_w: float,
) -> None:
    """
    Блок выгод — отвечает 'что я получаю?' до технической конфигурации.
    5 коротких пунктов, каждый — конкретная выгода под параметры заказа.
    """
    awning_t = params.get("awning_type", "standard")
    control = str(params.get("control", "electric") or "electric")
    sensor = str(params.get("sensor_type", "none") or "none")
    width_val = params.get("width", "")
    proj_val = params.get("projection", params.get("height", ""))
    size_str = f"{width_val}×{proj_val} м " if width_val and proj_val else ""

    b_s = ParagraphStyle("bi", fontName="Arial", fontSize=10,
        textColor=C_DARK, leading=15, leftIndent=4 * mm, spaceAfter=2 * mm)

    if awning_t == "zip":
        b1 = (
            f"☀️ <b>Защита от солнца и ветра со всех сторон</b> — "
            f"ZIP-маркиза {size_str}закрывает проём без зазоров по бокам."
        )
    elif awning_t == "storefront":
        b1 = (
            f"🏪 <b>Витрина снова работает на продажи</b> — "
            f"маркиза {size_str}убирает блики с стекла. "
            "Покупатели видят товары, а не своё отражение."
        )
    else:
        b1 = (
            f"☀️ <b>Комфорт на террасе в любую жару</b> — "
            f"маркиза {size_str}даёт тень там, где нужно, и убирается когда не нужна."
        )

    if control == "electric":
        b2 = (
            "🎛️ <b>Открывается и закрывается одной кнопкой</b> — "
            "электропривод с пультом управления уже включён в комплект."
        )
    else:
        b2 = (
            "🎛️ <b>Простое ручное управление</b> — "
            "пружинный механизм открывает и удерживает полотно без инструментов."
        )

    if sensor in ("radio", "speed"):
        b3 = (
            "🌬️ <b>Маркиза сворачивается при ветре автоматически</b> — "
            "датчик защитит конструкцию, даже когда вас нет дома."
        )
    elif awning_t == "storefront":
        b3 = (
            "🌡️ <b>Снижает температуру в помещении</b> — "
            "прямое солнце не попадает внутрь. "
            "Меньше работает кондиционер, ниже счёт за электричество."
        )
    else:
        b3 = (
            "🛡️ <b>Испанская механика + австрийская ткань</b> — "
            "Gaviota с 1973 года, Sattler 100+ лет на рынке."
        )

    b4 = (
        "🎨 <b>Ткань не выгорает 7+ лет</b> — австрийский Sattler, "
        "краситель в волокне, а не на поверхности. Гарантия на ткань 5 лет."
    )
    with_install = str(params.get("installation", "none") or "none") == "with"
    if with_install:
        b5 = (
            "🔧 <b>Всё включено и под ключ</b> — "
            "монтаж, обучение управлению и проверка всех функций вместе с вами."
        )
    else:
        b5 = (
            "📦 <b>Изготовление по расчёту</b> — "
            "в КП без монтажа: доставку и выезд бригады при необходимости "
            "согласуем отдельно с менеджером."
        )

    story.append(_section_header("ЧТО ВЫ ПОЛУЧАЕТЕ", s))
    story.append(Spacer(1, 2 * mm))
    for b in (b1, b2, b3, b4, b5):
        story.append(Paragraph(b, b_s))
    story.append(Spacer(1, 3 * mm))


def _append_value_justification_section(
    story: list,
    s: dict,
    total: float,
    content_w: float,
) -> None:
    """
    Обоснование цены — снимает ценовой шок сразу после суммы.
    Стоимость владения + сравнение с реальными альтернативами.
    """
    story.append(_section_header("ПОЧЕМУ ЭТА ЦЕНА — ВЫГОДНОЕ ВЛОЖЕНИЕ", s))
    story.append(Spacer(1, 2 * mm))

    years = 12
    per_month = total / (years * 12)
    per_day = total / (years * 365)
    pm_txt = f"{int(per_month):,}".replace(",", "\u00a0")

    story.append(Paragraph(
        f"Маркиза — это не трата, а вложение на <b>{years} лет</b>. "
        f"В пересчёте это всего <b>{pm_txt} руб./мес.</b> "
        f"или <b>{int(per_day)} руб./день</b> — дешевле чашки кофе в кафе. "
        "За эти деньги: комфорт каждый день, защита от зноя и дождя, "
        "и никакого выгоревшего тента на мусорке через сезон.",
        ParagraphStyle("vji", parent=s["body"], spaceAfter=3 * mm),
    ))

    h_s = ParagraphStyle("vh", fontName="Arial-Bold", fontSize=8.5, textColor=C_WHITE, leading=11)
    h_sr = ParagraphStyle("vhr", fontName="Arial-Bold", fontSize=8.5, textColor=C_WHITE, leading=11, alignment=TA_RIGHT)
    hl_s = ParagraphStyle("vhl", fontName="Arial-Bold", fontSize=9, textColor=C_ACCENT, leading=12)
    hl_r = ParagraphStyle("vhlr", fontName="Arial-Bold", fontSize=9, textColor=C_ACCENT, leading=12, alignment=TA_RIGHT)
    n_s = ParagraphStyle("vn", fontName="Arial", fontSize=9, textColor=C_DARK, leading=12)
    n_r = ParagraphStyle("vnr", fontName="Arial", fontSize=9, textColor=C_DARK, leading=12, alignment=TA_RIGHT)
    m_s = ParagraphStyle("vm", fontName="Arial-Italic", fontSize=8.5, textColor=C_MID, leading=12)
    m_r = ParagraphStyle("vmr", fontName="Arial-Italic", fontSize=8.5, textColor=C_MID, leading=12, alignment=TA_RIGHT)

    total_fmt = f"{int(total):,}".replace(",", "\u00a0") + "\u00a0руб."

    data = [
        [Paragraph("Вариант", h_s), Paragraph("Стоимость", h_sr),
         Paragraph("Срок службы", h_sr), Paragraph("Управление", h_sr)],
        [Paragraph("✅ Ваша маркиза (данное КП)", hl_s), Paragraph(total_fmt, hl_r),
         Paragraph("10–15 лет", hl_r), Paragraph("Автоматика + пульт", hl_r)],
        [Paragraph("Китайский аналог (Ozon / Wildberries)", n_s), Paragraph("от 30 000 руб.", n_r),
         Paragraph("1–3 года", n_r), Paragraph("Ручное (цепочка)", n_r)],
        [Paragraph("Тент или зонт", m_s), Paragraph("от 3 000 руб.", m_r),
         Paragraph("1–2 сезона", m_r), Paragraph("Ставить / снимать вручную", m_r)],
        [Paragraph("Строительный навес", m_s), Paragraph("от 120 000 руб.", m_r),
         Paragraph("постоянно", m_r), Paragraph("не убирается никогда", m_r)],
    ]

    cw = content_w
    tbl = Table(data, colWidths=[cw * 0.36, cw * 0.20, cw * 0.22, cw * 0.22])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_DARK),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fff3ee")),
        ("LINEABOVE", (0, 1), (-1, 1), 2, C_ACCENT),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        *[("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f9fafc"))
          for i in range(3, len(data), 2)],
    ]))
    story.append(tbl)
    story.append(Spacer(1, 5 * mm))


def _append_faq_section(story: list, s: dict, params: dict, content_w: float) -> None:
    """Закрытие возражений. Вопросы динамические — зависят от конфигурации заказа."""
    story.append(_section_header("ОТВЕЧАЕМ НА ЧАСТЫЕ ВОПРОСЫ", s))
    story.append(Spacer(1, 2 * mm))

    sensor = str(params.get("sensor_type", "none") or "none")
    awning_t = params.get("awning_type", "standard")
    control = str(params.get("control", "electric") or "electric")
    with_install = str(params.get("installation", "none") or "none") == "with"

    q_s = ParagraphStyle("fq", fontName="Arial-Bold", fontSize=9.5,
        textColor=C_DARK, leading=13, spaceAfter=1 * mm, spaceBefore=3 * mm)
    a_s = ParagraphStyle("fa", fontName="Arial", fontSize=9,
        textColor=C_DARK, leading=13, spaceAfter=1 * mm, leftIndent=4 * mm)

    faqs: list[tuple[str, str]] = []

    if awning_t == "storefront":
        faqs.append((
            "❓ Действительно ли маркиза убирает блики с витрины?",
            "Да. Блики появляются когда прямые солнечные лучи падают на стекло под острым углом. "
            "Маркиза создаёт тень перед окном — солнце больше не попадает прямо на стекло. "
            "Витрина становится прозрачной: покупатели видят товары, а не своё отражение. "
            "Особенно заметный эффект в утренние и вечерние часы, когда солнце низко.",
        ))
        faqs.append((
            "❓ Что даёт угол наклона 170° и стоит ли за него доплачивать?",
            "Стандартный угол 90° — козырёк горизонтально. Защищает от верхнего солнца. "
            "Угол 170° — локти опускаются почти вертикально, полотно закрывает окно как штора. "
            "Это актуально когда солнце низко (утро, вечер, зима) и бьёт прямо в стекло. "
            "Для магазинов с дорогими товарами, фотостудий, офисов — обычно стоит доплатить.",
        ))
        faqs.append((
            "❓ Можно ли нанести логотип на полотно маркизы?",
            "Да, это отдельная опция. Полноцветная латексная печать на акриловой ткани — "
            "принтер HP на водной основе, стойкость к внешним воздействиям. "
            "Маркиза с логотипом становится рекламным инструментом: "
            "её видно издалека, она работает на узнаваемость бренда. "
            "Стоимость и сроки уточните у менеджера.",
        ))

    if sensor in ("radio", "speed"):
        faqs.append((
            "❓ Датчик сработает при ветре, даже если меня нет дома?",
            "Да. Датчик крепится на конструкцию и отслеживает колебания полотна "
            "в нескольких направлениях (3D) — это не просто датчик скорости ветра, "
            "он чувствует саму вибрацию конструкции. Команда на сворачивание уходит "
            "по радиоканалу до того, как нагрузка достигнет опасного уровня. "
            "Всё автоматически, без интернета и вашего участия.",
        ))
    else:
        faqs.append((
            "❓ Что будет с маркизой при сильном ветре?",
            "При раскрытом полотне сильный порыв может повредить локти или разорвать ткань. "
            "Рекомендуем сворачивать при уходе из дома. "
            "Для полной автоматической защиты добавьте радиодатчик ветра — "
            "он стоит значительно меньше ремонта. Уточните у менеджера.",
        ))

    faqs.append((
        "❓ Ткань выгорит или потеряет цвет за пару лет?",
        "Нет, если это Sattler SUN-TEX. Краситель вводится в волокно ДО прядения — "
        "он внутри каждой нити, не на поверхности. Такой цвет не смывается и не выгорает. "
        "Гарантия на ткань — 5 лет. Австрийцы дают такой срок, "
        "потому что уверены в материале.",
    ))

    if control == "electric":
        if with_install:
            faqs.append((
                "❓ Сложно управлять? Нужно каждый раз что-то настраивать?",
                "Нет. Одна кнопка на пульте — открыто. Ещё раз — закрыто. "
                "Концевики в механизме сами останавливают полотно в нужных положениях. "
                "При установке настраиваем всё один раз и обучаем управлению — это 5 минут.",
            ))
        else:
            faqs.append((
                "❓ Сложно управлять? Нужно каждый раз что-то настраивать?",
                "Нет. Одна кнопка на пульте — открыто. Ещё раз — закрыто. "
                "Концевики в механизме сами останавливают полотно в нужных положениях. "
                "При заказе монтажа бригада настроит привод и обучит за несколько минут; "
                "без монтажа — по инструкции в комплекте.",
            ))

    if with_install:
        faqs.append((
            "❓ Монтаж — это дополнительные расходы или уже в цене?",
            "Монтаж включён — видите строку в детализации выше. "
            "Наши мастера занимаются только маркизами, не сантехники по совместительству. "
            "После установки: проверяем функции вместе с вами, обучаем, убираем за собой.",
        ))
    else:
        faqs.append((
            "❓ Монтаж в этот расчёт не входит — как быть?",
            "В детализации — изготовление (и доставка, если указана), без выезда монтажной бригады. "
            "Монтаж, замер на объекте и обучение управлению можно добавить — "
            "стоимость и сроки уточните у менеджера.",
        ))

    faqs.append((
        "❓ 80% предоплата — это нормально? Не рискованно?",
        "Нормально для штучного производства под заказ. "
        "Работаем официально: договор с реквизитами, кассовый чек, гарантийный талон. "
        "Вы защищены юридически с первого рубля.",
    ))

    if awning_t == "standard":
        faqs.append((
            "❓ Когда придётся менять маркизу и во сколько это обойдётся?",
            "Каркас Gaviota рассчитан на 10–15 лет. "
            "Ткань Sattler — 7–10 лет при уходе раз в сезон (промыть водой). "
            "Если ткань потеряет вид — меняют без замены каркаса. "
            "Это значительно дешевле, чем новая маркиза.",
        ))

    for question, answer in faqs:
        story.append(Paragraph(question, q_s))
        story.append(Paragraph(answer, a_s))

    story.append(Spacer(1, 4 * mm))


def _append_guarantees_block(story: list, s: dict, params: dict, content_w: float) -> None:
    """Блок доверия перед контактами. Social proof через цифры."""
    story.append(_section_header("НАШИ ГАРАНТИИ И ВАША ЗАЩИТА", s))
    story.append(Spacer(1, 2 * mm))

    with_install = str(params.get("installation", "none") or "none") == "with"
    guarantees: list[tuple[str, str]] = [
        ("✅ Официальный договор",
         "Все условия, сроки и цена — в документе. Вы защищены с первого рубля предоплаты."),
        ("✅ Гарантия 2 + 5 лет",
         "2 года на каркас, электрику и автоматику. "
         "5 лет на ткань Sattler — такой срок даёт только уверенный производитель."),
        ("✅ Gaviota, Испания — с 1973 года",
         "Более 50 лет производства маркиз, поставки в 40+ стран. Не новичок на рынке."),
        ("✅ Sattler, Австрия — более 100 лет",
         "Сертификат OEKO-TEX (безопасно для детей), поставки в 60+ стран мира."),
    ]
    if with_install:
        guarantees.append((
            "✅ Монтаж только нашей бригадой",
            "Специализация — только маркизы. "
            "Обучение и проверка всех функций после установки включены.",
        ))
    guarantees.append((
        "✅ Бесплатный замер",
        "Выедем на объект, измерим, покажем образцы тканей — бесплатно и без обязательств.",
    ))

    g_l = ParagraphStyle("gl", fontName="Arial-Bold", fontSize=9, textColor=C_DARK, leading=13)
    g_v = ParagraphStyle("gv", fontName="Arial", fontSize=9, textColor=C_DARK, leading=13)

    g_data = [[Paragraph(l, g_l), Paragraph(v, g_v)] for l, v in guarantees]
    g_tbl = Table(g_data, colWidths=[content_w * 0.38, content_w * 0.62])
    g_tbl.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, C_BORDER),
        *[("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f9fafc"))
          for i in range(1, len(g_data), 2)],
    ]))
    story.append(g_tbl)
    story.append(Spacer(1, 5 * mm))


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------

def generate_pdf(result: dict[str, Any], params: dict[str, Any] | None = None) -> io.BytesIO:
    """
    Генерирует PDF КП по результату расчёта.

    result: {total, rows, text}
    params: исходные параметры запроса (опционально, для секции конфигурации)
    """
    _ensure_fonts()
    if params is None:
        params = {}

    buf       = io.BytesIO()
    now       = datetime.now()
    date_str  = now.strftime("%d.%m.%Y")
    kp_number = now.strftime("%Y%m%d-%H%M")
    title     = f"КП {kp_number} — {COMPANY_NAME}"

    doc = _KPDoc(buf, title, kp_number, date_str)
    s   = _styles()

    content_w = PAGE_W - doc.leftMargin - doc.rightMargin
    story: list = []

    # ══════════════════════════════════════════════════════════════════════
    # СЕКЦИЯ 1 — ЗАГОЛОВОК ДОКУМЕНТА
    # ══════════════════════════════════════════════════════════════════════
    story.append(Paragraph("КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ", s["h1"]))

    rows_data = result.get("rows", [])
    total = result.get("total", 0)

    product_title = rows_data[0][0] if rows_data else "Маркиза"

    awning_t_label = {
        "standard": "локтевой маркизы",
        "storefront": "витринной маркизы",
        "zip": "ZIP-маркизы",
    }.get(params.get("awning_type", "standard"), "маркизы")

    width_val = params.get("width", "")
    proj_val = params.get("projection", params.get("height", ""))
    size_str = f"{width_val}×{proj_val} м " if width_val and proj_val else ""
    control_kw = (
        "с автоматическим управлением"
        if params.get("control") == "electric"
        else "с ручным управлением"
    )
    sensor_kw = (
        ", датчик ветра — маркиза убирается сама"
        if str(params.get("sensor_type", "none")) in ("radio", "speed")
        else ""
    )

    hook_style = ParagraphStyle("hook", fontName="Arial-Italic", fontSize=10.5,
        textColor=C_ACCENT, leading=15, spaceAfter=4 * mm)
    if params.get("awning_type") == "storefront":
        hook_text = (
            f"Витрина {size_str}без бликов, товар виден покупателям — "
            f"расчёт витринной маркизы {control_kw}."
        )
    else:
        hook_text = (
            f"Ваша терраса {size_str}под защитой от зноя и непогоды — "
            f"расчёт {awning_t_label} {control_kw}{sensor_kw}."
        )
    story.append(Paragraph(hook_text, hook_style))

    story.append(Paragraph(product_title, ParagraphStyle(
        "pt", fontName="Arial", fontSize=11, textColor=C_MID, spaceAfter=4 * mm)))

    _append_benefits_block(story, s, params, content_w)

    # Горизонтальный разделитель
    story.append(Table([[""]], colWidths=[content_w],
                       style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1, C_BORDER),
                                         ("TOPPADDING", (0, 0), (-1, -1), 0),
                                         ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm)])))

    # ══════════════════════════════════════════════════════════════════════
    # СЕКЦИЯ 2 — КОНФИГУРАЦИЯ ИЗДЕЛИЯ
    # ══════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 3 * mm))
    story.append(_section_header("КОНФИГУРАЦИЯ ИЗДЕЛИЯ", s))
    story.append(Spacer(1, 2 * mm))

    kv = _build_config_pairs(params, rows_data, result)
    if kv:
        story.append(_kv_table(kv, s))

    awning_t = params.get("awning_type", "")
    if awning_t in ("standard", "storefront"):
        _append_sattler_fabric_advantages(story, s)

    if awning_t == "standard":
        _append_elbow_arms_section(story, s, content_w)
    elif awning_t == "storefront":
        _append_storefront_arms_section(story, s, params, content_w)

    story.append(Spacer(1, 4 * mm))

    # ══════════════════════════════════════════════════════════════════════
    # СЕКЦИЯ 3 — ДЕТАЛИЗАЦИЯ СТОИМОСТИ
    # ══════════════════════════════════════════════════════════════════════
    story.append(_section_header("ДЕТАЛИЗАЦИЯ СТОИМОСТИ", s))
    story.append(Spacer(1, 2 * mm))

    # Заголовок таблицы
    hdr = [
        Paragraph("Позиция", s["tbl_header"]),
        Paragraph("Стоимость", s["tbl_header_r"]),
    ]
    tbl_data = [hdr]

    col_price_w = 46 * mm
    col_name_w  = content_w - col_price_w

    for i, row in enumerate(rows_data):
        label, value = row[0], row[1]
        is_total_row = (i == len(rows_data) - 1) and ("итог" in label.lower() or "всего" in label.lower())

        row_name_s = ParagraphStyle(
            f"rn{i}",
            fontName="Arial-Bold" if is_total_row else "Arial",
            fontSize=9.5, textColor=C_DARK, leading=13
        )
        if value == 0:
            val_p = Paragraph("включено", s["tbl_zero"])
        else:
            row_val_s = ParagraphStyle(
                f"rv{i}",
                fontName="Arial-Bold" if is_total_row else "Arial",
                fontSize=9.5, textColor=C_ACCENT if is_total_row else C_DARK,
                alignment=TA_RIGHT, leading=13
            )
            val_p = Paragraph(_fmt(value), row_val_s)

        tbl_data.append([Paragraph(label, row_name_s), val_p])

    price_tbl = Table(tbl_data, colWidths=[col_name_w, col_price_w], repeatRows=1)

    n = len(tbl_data)
    price_tbl.setStyle(TableStyle([
        # Заголовок
        ("BACKGROUND",    (0, 0), (-1, 0),  C_DARK),
        ("TOPPADDING",    (0, 0), (-1, 0),  3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  3 * mm),
        ("LEFTPADDING",   (0, 0), (-1, 0),  3 * mm),
        ("RIGHTPADDING",  (0, 0), (-1, 0),  3 * mm),
        # Строки данных
        ("TOPPADDING",    (0, 1), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2.5 * mm),
        ("LEFTPADDING",   (0, 1), (-1, -1), 3 * mm),
        ("RIGHTPADDING",  (0, 1), (-1, -1), 3 * mm),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        # Разделители
        ("LINEBELOW",     (0, 1), (-1, n - 2), 0.5, C_BORDER),
        # Чередование строк
        *[("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f9fafc"))
          for i in range(2, n, 2)],
    ]))
    story.append(price_tbl)
    story.append(Spacer(1, 3 * mm))

    # ── ИТОГО: большой баннер ─────────────────────────────────────────────
    total_data = [[
        Paragraph("ИТОГО К ОПЛАТЕ:", s["total_label"]),
        Paragraph(_fmt(total), s["total_value"]),
    ]]
    # Для баннера ИТОГО расширяем ценовую колонку до 54 мм (больший шрифт + "руб.")
    total_price_w = 54 * mm
    total_name_w  = content_w - total_price_w
    total_tbl = Table(total_data, colWidths=[total_name_w, total_price_w])
    total_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_DARK),
        ("TOPPADDING",    (0, 0), (-1, -1), 4.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5 * mm),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4 * mm),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        # Оранжевая полоска сверху
        ("LINEABOVE",     (0, 0), (-1, 0),  3, C_ACCENT),
    ]))
    story.append(KeepTogether([total_tbl]))
    story.append(Spacer(1, 5 * mm))

    _append_value_justification_section(story, s, total, content_w)

    # ══════════════════════════════════════════════════════════════════════
    # СЕКЦИЯ 4 — УСЛОВИЯ ПРЕДЛОЖЕНИЯ
    # ══════════════════════════════════════════════════════════════════════
    story.append(_section_header("УСЛОВИЯ ПРЕДЛОЖЕНИЯ", s))
    story.append(Spacer(1, 2 * mm))

    terms = [
        ("📅", "Действительность КП:", "10 дней с даты выставления"),
        ("🏭", "Срок изготовления:", "3 недели после оплаты (май–июль: до 5–6 недель)"),
        ("✅", "Гарантия:", "2 года на конструкцию и электрику, 5 лет на ткань Sattler"),
        ("💳", "Условия оплаты:", "80% при подтверждении заказа, 20% перед отгрузкой"),
    ]
    if str(params.get("installation", "none") or "none") == "with":
        terms.append((
            "🔧",
            "После монтажа:",
            "Обучение управлению + проверка всех функций включена",
        ))
    terms.append((
        "📐",
        "Замер:",
        "Бесплатный выезд для уточнения параметров перед договором",
    ))

    terms_data = []
    for _ico, lbl, val in terms:
        terms_data.append([
            Paragraph(lbl, ParagraphStyle("tl", fontName="Arial-Bold", fontSize=9,
                                          textColor=C_DARK, leading=13)),
            Paragraph(val, ParagraphStyle("tv", fontName="Arial", fontSize=9,
                                          textColor=C_DARK, leading=13)),
        ])

    t_col1 = content_w * 0.38
    t_col2 = content_w * 0.62
    terms_tbl = Table(terms_data, colWidths=[t_col1, t_col2])
    terms_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2 * mm),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.5, C_BORDER),
        *[("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f9fafc"))
          for i in range(1, len(terms_data), 2)],
    ]))
    story.append(terms_tbl)
    story.append(Spacer(1, 5 * mm))

    _append_faq_section(story, s, params, content_w)

    # ══════════════════════════════════════════════════════════════════════
    # СЕКЦИЯ 5 — ИЗОБРАЖЕНИЯ (схема короба + образец ткани)
    # ══════════════════════════════════════════════════════════════════════
    scheme_path = _get_scheme_image(params)
    scheme_caption = "Схема короба"
    decolife = result.get("decolife") or {}
    dl_show = _static_url_to_fs(decolife.get("thumbnail", ""))
    if dl_show:
        scheme_path = dl_show
        scheme_caption = decolife.get("series_display") or (decolife.get("series") or "").replace("Decolife", "Gaviota") or "Модель Gaviota"
    elif params.get("awning_type") == "standard":
        scheme_caption = "Тип конструкции"

    fabric_img = _get_fabric_image(params)
    fabric_caption = _fabric_sample_caption_for_pdf(params)

    if scheme_path or fabric_img:
        story.append(_section_header("ЭСКИЗ И ОБРАЗЕЦ ТКАНИ", s))
        story.append(Spacer(1, 3 * mm))

        gap = 5 * mm
        img_cells: list = []
        if scheme_path and fabric_img:
            # Эскиз — большая колонка и высота, чтобы читались детали на рендере серии
            scheme_col_w = (content_w - gap) * 0.66
            fabric_col_w = content_w - gap - scheme_col_w
            scheme_max_w = scheme_col_w - 2 * mm
            scheme_max_h = 172 * mm
            fabric_max_w = fabric_col_w - 2 * mm
            fabric_max_h = min(128 * mm, fabric_max_w * 1.2)
            img_cells.append(
                _image_card(
                    scheme_path,
                    scheme_caption,
                    max_w=scheme_max_w,
                    s=s,
                    max_h=scheme_max_h,
                )
            )
            img_cells.append(
                _image_card(
                    fabric_img,
                    fabric_caption,
                    max_w=fabric_max_w,
                    s=s,
                    max_h=fabric_max_h,
                )
            )
            imgs_tbl = Table(
                [img_cells],
                colWidths=[scheme_col_w, fabric_col_w],
            )
            imgs_tbl.setStyle(TableStyle([
                ("VALIGN",       (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING",  (0, 0), (-1, -1), 1 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("TOPPADDING",   (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
            ]))
            story.append(imgs_tbl)
        elif scheme_path:
            story.append(
                _image_card(
                    scheme_path,
                    scheme_caption,
                    max_w=content_w - 4 * mm,
                    s=s,
                    max_h=182 * mm,
                )
            )
        elif fabric_img:
            story.append(
                _image_card(
                    fabric_img,
                    fabric_caption,
                    max_w=content_w - 4 * mm,
                    s=s,
                    max_h=140 * mm,
                )
            )

        story.append(Spacer(1, 5 * mm))

    _append_selected_equipment_section(story, s, params, content_w)

    # Воздух перед блоком гарантий (после текста/картинок автоматики и LED)
    story.append(Spacer(1, 9 * mm))

    _append_guarantees_block(story, s, params, content_w)

    # ══════════════════════════════════════════════════════════════════════
    # СЕКЦИЯ 6 — КОНТАКТЫ
    # ══════════════════════════════════════════════════════════════════════
    story.append(_section_header("КАК С НАМИ СВЯЗАТЬСЯ", s))
    story.append(Spacer(1, 2 * mm))

    contacts = [
        ("Сайт", COMPANY_SITE),
        ("E-mail", COMPANY_EMAIL),
        ("Телефон", COMPANY_PHONE),
    ]
    story.append(_kv_table(contacts, s))

    story.append(Spacer(1, 3 * mm))
    story.append(Table([[""]], colWidths=[content_w], style=TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 1, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ])))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "⚡ Следующий шаг: позвоните или напишите — "
        "приедем на бесплатный замер и привезём образцы тканей вживую.",
        ParagraphStyle("cta", fontName="Arial-Bold", fontSize=10,
            textColor=C_ACCENT, leading=14, spaceAfter=2 * mm),
    ))
    story.append(Paragraph(
        "КП действительно 10 дней. Каждую неделю сезона (апрель–май) "
        "сроки изготовления увеличиваются на 3–5 дней. Сейчас — 3 недели.",
        ParagraphStyle("cta_sub", fontName="Arial-Italic", fontSize=8.5,
            textColor=C_MID, leading=12, spaceAfter=0),
    ))

    story.append(Paragraph(
        get_pdf_label(
            "disclaimer",
            "Расчёт предварительный. Цена фиксируется в договоре после замера — "
            "никаких скрытых доплат после подписания.",
        ),
        s["note"],
    ))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"{COMPANY_PHONE}  ·  {COMPANY_EMAIL}  ·  {COMPANY_SITE}",
        ParagraphStyle("final_cta", fontName="Arial-Bold", fontSize=9,
            textColor=C_ACCENT, alignment=TA_CENTER, leading=13),
    ))

    doc.build(story)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Формирование пар ключ-значение для секции конфигурации
# ---------------------------------------------------------------------------

_AWNING_TYPE_LABELS = {
    "standard":   "Локтевая маркиза (складывается полностью)",
    "storefront": "Витринная маркиза (для фасадов и витрин)",
    "zip":        "ZIP-маркиза (боковые направляющие, защита от ветра)",
}
_CONFIG_LABELS = {
    "open":     "Открытая (механизм и вал открыты, экономичный вариант)",
    "semi":     "Полукассетная (механизм частично защищён коробом)",
    "cassette": "Кассетная (полотно и механизм убираются в короб полностью)",
    "g400":     "G400 Italy — открытая витринная (Gaviota)",
    "g450":     "G450 Desert — кассетная витринная (Gaviota)",
    "zip100":   "ZIP 100 (ширина до 4 м)",
    "zip130":   "ZIP 130 (усиленная, ширина до 6 м)",
}
_FABRIC_LABELS = {
    "gaviota":  "Sattler Gaviota (базовая)",
    "elements": "Sattler Elements (+5%)",
    "solids":   "Sattler Solids (+5%)",
    "lumera":   "Sattler Lumera (+10%)",
    "lumera3d": "Sattler Lumera 3D (+10%)",
    "veozip":   "Screen Veosol / Veozip",
    "soltis":   "Screen Soltis 86/92",
    "copaco":   "Screen Copaco",
}
# Серии SUN-TEX для строки «Ткань» в КП (без пометок наценки)
_STD_FABRIC_SUNTEX_SERIES: dict[str, str] = {
    "gaviota": "Gaviota",
    "elements": "Sattler Elements",
    "solids": "Sattler Solids",
    "lumera": "Sattler Lumera",
    "lumera3d": "Sattler Lumera 3D",
}
_STD_FABRIC_MFG = "Sattler SUN-TEX"
_ZIP_FABRIC_MFG: dict[str, str] = {
    "veozip": "Serge Ferrari",
    "soltis": "Serge Ferrari",
    "copaco": "Copaco Screenweavers",
}
_CONTROL_LABELS = {
    "manual":   "Ручное (пружинный механизм, цепочка)",
    "electric": "Электропривод (управление с пульта)",
}
_MOTOR_LABELS = {
    "somfy":    "Somfy",
    "simu":     "Simu",
    "decolife": "Gaviota",
}
_COLOR_LABELS_STD = {
    "white":      "RAL 9016 глянец белый",
    "brown":      "RAL 8014 коричневый (глянец / муар текстур.) +5%",
    "anthracite": "RAL 7016 муар текстур. антрацит +5%",
    "custom":     "Специальный RAL +12%",
}
# G400 / G450 — прайс Decolife G400 Italy
_COLOR_LABELS_STOREFRONT = {
    "white":      "RAL 9016 глянец белый",
    "brown":      "RAL 8014 муар / глянец коричневый",
    "ral9005":    "RAL 9005 муар",
    "anthracite": "RAL 7016 муар текстур. антрацит (+10%)",
    "ral9t08":    "RAL 9T08 муар (+10%)",
    "custom":     "Специальный RAL (+12%)",
}
_COLOR_LABELS_ZIP = {
    "ral9016": "RAL 9016 Матовый белый",
    "ral7024": "RAL 7024 Матовый серый",
    "ral9t08": "RAL 9T08 Текстурированный графит",
    "ral8028": "RAL 8028 Муар коричневый",
    "custom":  "Специальный RAL (+10%)",
}


def _fabric_sample_caption_for_pdf(params: dict[str, Any]) -> str:
    """Подпись под миниатюрой ткани в блоке «Эскиз и образец ткани»."""
    awning_type = params.get("awning_type", "")
    if awning_type == "zip":
        fz = params.get("fabric_zip", "")
        if not fz:
            return "Образец ткани"
        fabric_name = _FABRIC_LABELS.get(fz, fz)
        mfg_z = _ZIP_FABRIC_MFG.get(fz)
        if mfg_z:
            fabric_name = f"{mfg_z} · {fabric_name}"
        color_art = (
            params.get("veozip_color")
            or params.get("soltis_color")
            or params.get("copaco_color")
            or ""
        )
        col_name = params.get("soltis_collection") or params.get("copaco_collection") or ""
        parts: list[str] = [fabric_name]
        if col_name:
            parts.append(str(col_name))
        if color_art:
            parts.append(f"арт. {color_art}")
        return " · ".join(parts)

    fb = params.get("fabric", "")
    swatch_lbl = (params.get("fabric_color_label") or params.get("fabric_swatch_label") or "").strip()
    series = _STD_FABRIC_SUNTEX_SERIES.get(fb, _FABRIC_LABELS.get(fb, fb))
    parts2: list[str] = [_STD_FABRIC_MFG, f"«{series}»"]
    if swatch_lbl:
        parts2.append(f"арт. {swatch_lbl}")
    if fb or swatch_lbl:
        return " · ".join(parts2)
    return "Образец ткани"


def _build_config_pairs(
    params: dict[str, Any],
    rows: list[list],
    result: dict[str, Any] | None = None,
) -> list[tuple[str, str]]:
    """Строит список (ключ, значение) для секции конфигурации."""
    pairs: list[tuple[str, str]] = []

    awning_type = params.get("awning_type", "")
    config      = params.get("config", "")

    if awning_type:
        pairs.append(("Тип маркизы", _AWNING_TYPE_LABELS.get(awning_type, awning_type)))

    if config:
        pairs.append(("Конструкция", _CONFIG_LABELS.get(config, config)))

    # Размеры
    if awning_type == "zip":
        w = params.get("width")
        h = params.get("height")
        if w and h:
            pairs.append(("Ширина × Высота", f"{w} × {h} м"))
    else:
        w = params.get("width")
        p = params.get("projection")
        if w and p:
            pairs.append(("Ширина × Вылет", f"{w} × {p} м"))

    qty = params.get("quantity", 1)
    if int(qty) > 1:
        pairs.append(("Количество", str(qty)))

    if awning_type == "storefront":
        st_tilt = params.get("storefront_tilt_170")
        tilt_on = st_tilt in (True, "true", 1, "1", "yes", "on")
        pairs.append((
            "Угол наклона",
            "170° (локти вертикально, +15%)" if tilt_on else "90° стандартный",
        ))

    st_val = str(params.get("storefront_valance", "none") or "none").strip().lower()
    if awning_type == "storefront" and st_val == "straight":
        pairs.append(("Волан", "Прямой 150 мм"))
    elif awning_type == "storefront" and st_val == "shaped":
        pairs.append(("Волан", "Фигурный 150 мм"))

    # Ткань
    if awning_type == "zip":
        fz = params.get("fabric_zip", "")
        if fz:
            fabric_name = _FABRIC_LABELS.get(fz, fz)
            mfg_z = _ZIP_FABRIC_MFG.get(fz)
            if mfg_z:
                fabric_name = f"{mfg_z} · {fabric_name}"
            # добавляем артикул
            color_art = (params.get("veozip_color") or
                         params.get("soltis_color") or
                         params.get("copaco_color") or "")
            col_name = (params.get("soltis_collection") or
                        params.get("copaco_collection") or "")
            if col_name:
                fabric_name += f" / {col_name}"
            if color_art:
                fabric_name += f" (арт. {color_art})"
            pairs.append(("Ткань", fabric_name))
    else:
        fb = params.get("fabric", "")
        swatch_lbl = (params.get("fabric_color_label") or params.get("fabric_swatch_label") or "").strip()
        series = _STD_FABRIC_SUNTEX_SERIES.get(fb, _FABRIC_LABELS.get(fb, fb))
        parts: list[str] = [_STD_FABRIC_MFG, f"серия «{series}»"]
        if swatch_lbl:
            parts.append(f"арт. {swatch_lbl}")
        if fb or swatch_lbl:
            pairs.append(("Ткань", " · ".join(parts)))

    # Цвет каркаса (спец. RAL — номер из каталога в заявке)
    def _frame_color_label_zip(fc: str) -> str:
        if fc == "custom":
            ral = str(params.get("frame_custom_ral") or "").strip()
            rnm = str(params.get("frame_custom_ral_name") or "").strip()
            if ral:
                tail = f" ({rnm})" if rnm else ""
                return f"RAL {ral}{tail} — специальный цвет (+10%)"
        return _COLOR_LABELS_ZIP.get(fc, fc)

    def _frame_color_label_std(fc: str) -> str:
        if fc == "custom":
            ral = str(params.get("frame_custom_ral") or "").strip()
            rnm = str(params.get("frame_custom_ral_name") or "").strip()
            if ral:
                tail = f" ({rnm})" if rnm else ""
                return f"RAL {ral}{tail} — специальный цвет (+12%)"
        if awning_type == "storefront":
            return _COLOR_LABELS_STOREFRONT.get(fc, fc)
        return _COLOR_LABELS_STD.get(fc, fc)

    if awning_type == "zip":
        fc = params.get("frame_color_zip", "")
        if fc:
            pairs.append(("Цвет каркаса", _frame_color_label_zip(fc)))
    else:
        fc = params.get("frame_color", "")
        if fc:
            pairs.append(("Цвет каркаса", _frame_color_label_std(fc)))

    # Комплектация по прайсу Gaviota/Decolife (строки «Кол-во кронштейнов», «Поддержек вала»)
    dl = (result or {}).get("decolife") or {}
    if awning_type == "standard" and dl:
        bc = dl.get("bracket_count")
        ssc = dl.get("shaft_support_count")
        if bc is not None:
            pairs.append(("Кронштейны крепления", f"{int(float(bc))} шт."))
        if ssc is not None:
            pairs.append(("Поддержки вала", f"{int(float(ssc))} шт."))

    # Управление
    ctrl = params.get("control", "")
    ctrl_electric = str(params.get("control", "") or "").lower() == "electric"
    if ctrl:
        ctrl_label = _CONTROL_LABELS.get(ctrl, ctrl)
        if ctrl == "electric":
            mb = params.get("motor_brand", "")
            if mb:
                ctrl_label += f" {_MOTOR_LABELS.get(mb, mb)}"
        pairs.append(("Управление", ctrl_label))

    rc = (result or {}).get("remote_commercial") or {}
    if ctrl_electric and rc.get("label"):
        pairs.append(("Пульт управления", str(rc["label"])))

    # Датчик (модель зависит от бренда автоматики; ZIP в калькуляторе без датчиков)
    sensor = params.get("sensor_type", "none")
    if (
        sensor
        and sensor != "none"
        and ctrl_electric
        and awning_type != "zip"
    ):
        mb = params.get("motor_brand", "decolife")
        spair = get_sensor_pdf_pair(str(mb), str(sensor))
        if spair:
            pairs.append(spair)

    # Подсветка
    light = params.get("lighting_option", "none")
    if light and light != "none":
        pairs.append(("Подсветка", "LED встроенная"))

    # Установка
    inst = params.get("installation", "none")
    if inst == "with":
        pairs.append(("Монтаж", "Включён в стоимость"))

    return pairs
