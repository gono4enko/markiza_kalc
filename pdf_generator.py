"""
Генерация коммерческого предложения (КП) для маркиз.
Формат А4, две страницы, фирменный стиль Pergolamarket.
"""

import io
import os
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
    "В расчёте используется маркизное полотно <b>Sattler SUN-TEX</b> (группа Sattler, Европа) — "
    "специализированные солнцезащитные текстили. Кратко о свойствах:"
)
_SATTLER_ADV_BULLETS: tuple[str, ...] = (
    "100% <b>solution-dyed акрил</b>: цвет в массе волокна, высокая устойчивость к выцветанию и длительной УФ-нагрузке.",
    "Испытания по <b>UV Standard 801</b> с моделированием эксплуатации; для солнцезащитных текстилей Sattler типичен "
    "УФ-фактор <b>40–80</b> — существенно выше обычной хлопковой ткани в тени.",
    "Отделка <b>TEXgard</b> / <b>TEXgard OEKO CLEAN</b>: вода и грязь отталкиваются, поддерживается эффект самоочищения; "
    "соответствие <b>OEKO-TEX</b>, отделка <b>без PFAS</b>.",
    "В коллекциях <b>Lumera</b> и <b>Lumera 3D</b> — волокно <b>CBA</b> (Clean Brilliant Acrylic), разработанное для Sattler: "
    "более гладкая «сияющая» поверхность и насыщенность цвета.",
    "Линейка <b>Lumera All Weather</b> с покрытием <b>IPC</b>: повышенная защита от влаги при сохранении мягкости полотна.",
    "Серия <b>Elements Cross Fiber</b>: использование переработанной пряжи из переходных зон окраски — ответственное "
    "использование сырья при сохранении внешнего вида и качества.",
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


def _append_elbow_arms_section(story: list, s: dict[str, ParagraphStyle], content_w: float) -> None:
    """Секция про тип локтей, сечение и натяжение — только для локтевой маркизы."""
    story.append(Spacer(1, 3 * mm))
    story.append(_section_header("ЛОКТИ И НАТЯЖЕНИЕ ПОЛОТНА", s))
    story.append(Spacer(1, 2 * mm))

    ps_body = ParagraphStyle("elbow_body", parent=s["body"], spaceAfter=2 * mm)
    story.append(Paragraph(
        "Складные плечи (локти) воспринимают нагрузку от ветра и веса полотна. С ростом <b>вылета</b> возрастают требования к "
        "<b>сечению профиля</b> и <b>системе натяжения</b> — это влияет на провисание ткани и ветроустойчивость.",
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
        "* Ориентир по каталогам комплектующих; фактический предел зависит от ширины, крепления и условий эксплуатации.",
        ParagraphStyle("elbow_foot", parent=s["small"], spaceBefore=1.5 * mm, spaceAfter=0),
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


def _get_fabric_image(params: dict[str, Any]) -> str | None:
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

    return None


def _first_file(folder: str) -> str | None:
    """Возвращает первый .jpg файл в папке или None."""
    if not os.path.isdir(folder):
        return None
    for f in sorted(os.listdir(folder)):
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            return os.path.join(folder, f)
    return None


def _image_card(
    img_path: str,
    caption: str,
    max_w: float,
    s: dict,
    max_h: float | None = None,
) -> Table:
    """Возвращает ячейку-блок с изображением (пропорции сохранены) и подписью."""
    if max_h is None:
        max_h = max_w
    try:
        # Читаем реальные размеры через Pillow чтобы сохранить пропорции
        from PIL import Image as PILImage
        with PILImage.open(img_path) as pil:
            native_w, native_h = pil.size

        ratio = native_w / native_h
        # Вписываем в прямоугольник max_w × max_h
        if ratio >= max_w / max_h:
            draw_w = max_w
            draw_h = max_w / ratio
        else:
            draw_h = max_h
            draw_w = max_h * ratio

        img = Image(img_path, width=draw_w, height=draw_h)
        img.hAlign = "CENTER"
        card_w = draw_w
    except Exception:
        return Table([[Paragraph(caption, s["small"])]])
    
    card_w = max_w  # ячейка всегда одной ширины для выравнивания

    caption_p = Paragraph(caption, ParagraphStyle(
        "img_cap",
        fontName="Arial",
        fontSize=7.5,
        textColor=C_MID,
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

    rows_data  = result.get("rows", [])
    total      = result.get("total", 0)

    # Определяем заголовок изделия из первой строки rows
    product_title = rows_data[0][0] if rows_data else "Маркиза"
    story.append(Paragraph(product_title, ParagraphStyle(
        "pt", fontName="Arial", fontSize=11, textColor=C_MID, spaceAfter=4 * mm)))

    # Горизонтальный разделитель
    story.append(Table([[""]], colWidths=[content_w],
                       style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1, C_BORDER),
                                         ("TOPPADDING", (0,0),(-1,-1), 0),
                                         ("BOTTOMPADDING",(0,0),(-1,-1), 2*mm)])))

    # ══════════════════════════════════════════════════════════════════════
    # СЕКЦИЯ 2 — КОНФИГУРАЦИЯ ИЗДЕЛИЯ + визуальные изображения
    # ══════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 3 * mm))
    story.append(_section_header("КОНФИГУРАЦИЯ ИЗДЕЛИЯ", s))
    story.append(Spacer(1, 2 * mm))

    kv = _build_config_pairs(params, rows_data)
    if kv:
        story.append(_kv_table(kv, s))

    awning_t = params.get("awning_type", "")
    if awning_t in ("standard", "storefront"):
        _append_sattler_fabric_advantages(story, s)

    if awning_t == "standard":
        _append_elbow_arms_section(story, s, content_w)

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

    # ══════════════════════════════════════════════════════════════════════
    # СЕКЦИЯ 4 — УСЛОВИЯ И ГАРАНТИИ
    # ══════════════════════════════════════════════════════════════════════
    story.append(_section_header("УСЛОВИЯ ПРЕДЛОЖЕНИЯ", s))
    story.append(Spacer(1, 2 * mm))

    terms = [
        ("📅", "Действительность КП:", "10 дней с даты выставления"),
        ("🏭", "Срок изготовления:",    "3 недели после оплаты"),
        ("✅", "Гарантия:",             "2 года на конструкцию, 5 лет на ткань"),
        ("💳", "Условия оплаты:",       "80% предоплата, 20% перед отгрузкой"),
    ]

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

    fabric_path = _get_fabric_image(params)

    if scheme_path or fabric_path:
        story.append(_section_header("ЭСКИЗ И ОБРАЗЕЦ ТКАНИ", s))
        story.append(Spacer(1, 3 * mm))

        gap = 6 * mm
        col_w = (content_w - gap) / 2
        # Схема высокая (portrait) → ограничиваем высоту; ткань — квадрат
        img_cells = []
        if scheme_path:
            img_cells.append(_image_card(scheme_path, scheme_caption,
                                         max_w=col_w - 2 * mm, s=s, max_h=110 * mm))
        if fabric_path:
            img_cells.append(_image_card(fabric_path, "Образец ткани",
                                         max_w=col_w - 2 * mm, s=s, max_h=col_w - 2 * mm))

        if len(img_cells) == 2:
            imgs_tbl = Table(
                [img_cells],
                colWidths=[col_w, col_w],
            )
            imgs_tbl.setStyle(TableStyle([
                ("VALIGN",       (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING",  (0, 0), (-1, -1), 1 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("TOPPADDING",   (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
            ]))
            story.append(imgs_tbl)
        elif img_cells:
            story.append(img_cells[0])

        story.append(Spacer(1, 5 * mm))

    # ══════════════════════════════════════════════════════════════════════
    # СЕКЦИЯ 6 — КОНТАКТЫ
    # ══════════════════════════════════════════════════════════════════════
    story.append(_section_header("КАК С НАМИ СВЯЗАТЬСЯ", s))
    story.append(Spacer(1, 2 * mm))

    contacts = [
        ("Сайт",    COMPANY_SITE),
        ("E-mail",  COMPANY_EMAIL),
        ("Телефон", COMPANY_PHONE),
    ]
    story.append(_kv_table(contacts, s))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph(
        "Расчёт является предварительным коммерческим предложением. "
        "Итоговая стоимость определяется после замера и согласования проекта с менеджером.",
        s["note"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Формирование пар ключ-значение для секции конфигурации
# ---------------------------------------------------------------------------

_AWNING_TYPE_LABELS = {
    "standard":   "Локтевая маркиза",
    "storefront": "Витринная маркиза",
    "zip":        "ZIP-маркиза (рулонная)",
}
_CONFIG_LABELS = {
    "open":     "Открытая",
    "semi":     "Полукассетная",
    "cassette": "Кассетная",
    "g400":     "G400 Italy открытая (Gaviota)",
    "g450":     "G450 Desert кассетная (Gaviota)",
    "zip100":   "ZIP 100",
    "zip130":   "ZIP 130",
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
    "manual":   "Ручное",
    "electric": "Электропривод",
}
_MOTOR_LABELS = {
    "somfy":    "Somfy",
    "simu":     "Simu",
    "decolife": "Decolife",
}
_SENSOR_LABELS = {
    "none":  "—",
    "radio": "Датчик ветровых колебаний",
    "speed": "Датчик ветра и солнца",
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


def _build_config_pairs(
    params: dict[str, Any],
    rows: list[list],
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

    st_tilt = params.get("storefront_tilt_170")
    if awning_type == "storefront" and st_tilt in (True, "true", 1, "1", "yes", "on"):
        pairs.append(("Угол наклона", "до 170° (+15% к базе)"))

    st_val = str(params.get("storefront_valance", "none") or "none").strip().lower()
    if awning_type == "storefront" and st_val == "straight":
        pairs.append(("Волан", "прямой, 10 €/п.м ширины"))
    elif awning_type == "storefront" and st_val == "shaped":
        pairs.append(("Волан", "фигурный, 15 €/п.м ширины"))

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

    # Цвет каркаса
    if awning_type == "zip":
        fc = params.get("frame_color_zip", "")
        if fc:
            pairs.append(("Цвет каркаса", _COLOR_LABELS_ZIP.get(fc, fc)))
    else:
        fc = params.get("frame_color", "")
        if fc:
            if awning_type == "storefront":
                pairs.append(("Цвет каркаса", _COLOR_LABELS_STOREFRONT.get(fc, fc)))
            else:
                pairs.append(("Цвет каркаса", _COLOR_LABELS_STD.get(fc, fc)))

    # Управление
    ctrl = params.get("control", "")
    if ctrl:
        ctrl_label = _CONTROL_LABELS.get(ctrl, ctrl)
        if ctrl == "electric":
            mb = params.get("motor_brand", "")
            if mb:
                ctrl_label += f" {_MOTOR_LABELS.get(mb, mb)}"
        pairs.append(("Управление", ctrl_label))

    # Датчик
    sensor = params.get("sensor_type", "none")
    if sensor and sensor != "none":
        pairs.append(("Датчик", _SENSOR_LABELS.get(sensor, sensor)))

    # Подсветка
    light = params.get("lighting_option", "none")
    if light and light != "none":
        pairs.append(("Подсветка", "LED встроенная"))

    # Установка
    inst = params.get("installation", "none")
    if inst == "with":
        pairs.append(("Монтаж", "Включён в стоимость"))

    return pairs
