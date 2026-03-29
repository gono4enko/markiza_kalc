"""
Расчётная логика маркиз — Python-порт calculate() из calculator_awning_v2_16.html.

Исправляет баг T-001: значения fabric используют ключи 'elements', 'lumera',
'solids', 'lumera3d' (соответствуют <option value="..."> в HTML),
а не 'sattler_elements' / 'sattler_lumera' из оригинального багованного JS.
"""

import math
import json
import os
from typing import Any


def _load_pricing() -> dict[str, Any]:
    """Загружает прайс из JSON-файла относительно этого модуля."""
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "static", "data", "awning_pricing.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_PRICING: dict[str, Any] | None = None


def get_pricing() -> dict[str, Any]:
    global _PRICING
    if _PRICING is None:
        _PRICING = _load_pricing()
    return _PRICING


def reload_pricing() -> dict[str, Any]:
    global _PRICING
    _PRICING = _load_pricing()
    return _PRICING


def next_std(v: float) -> float:
    """Округление вверх с шагом 0.5 м для попадания в ячейку таблицы."""
    return math.ceil(v / 0.5) * 0.5


def get_price(table: dict[str, Any], w: float, p: float) -> float:
    """
    Находит цену в матрице по ширине w и вылету/высоте p.
    Выбирает ближайшее значение ≥ w и ≥ p (или максимальное, если выходит за границу).
    """
    widths = sorted(float(k) for k in table.keys())
    sw = next((wv for wv in widths if wv >= w), widths[-1])
    row = table[str(sw)] if str(sw) in table else table[f"{sw:.1f}"]
    projs = sorted(float(k) for k in row.keys())
    sp = next((pv for pv in projs if pv >= p), projs[-1])
    key = str(sp) if str(sp) in row else f"{sp:.1f}"
    return row.get(key, 0)


# Метки для текстового описания
_CONFIG_NAMES = {
    "open": "открытая",
    "semi": "полукассетная",
    "cassette": "кассетная",
    "g400": "G400",
    "g450": "G450",
    "zip100": "ZIP 100",
    "zip130": "ZIP 130",
}

_MOTOR_NAMES = {
    "somfy": "Somfy",
    "simu": "Simu",
    "decolife": "Decolife",
}

_TYPE_NAMES = {
    "standard": "Локтевая",
    "storefront": "Витринная",
    "zip": "ZIP",
}


def calculate(params: dict[str, Any]) -> dict[str, Any]:
    """
    Выполняет расчёт стоимости маркизы.

    Параметры (params):
      awning_type: 'standard' | 'storefront' | 'zip'
      config: 'open'|'semi'|'cassette' (standard), 'g400'|'g450' (storefront), 'zip100'|'zip130' (zip)
      width: float (ширина, м)
      projection: float (вылет, м) — для standard/storefront
      height: float (высота, м) — для zip
      fabric: 'gaviota'|'elements'|'solids'|'lumera'|'lumera3d' — для standard/storefront
      fabric_zip: 'veozip'|'soltis' — для zip
      frame_color: 'white'|'brown'|'anthracite'|'custom' — для standard/storefront
      frame_color_zip: 'white'|'brown'|'custom' — для zip
      control: 'manual' | 'electric'
      motor_brand: 'somfy' | 'simu' | 'decolife'
      sensor_type: 'none' | 'radio' | 'speed'
      lighting_option: 'none' | 'standard'
      installation: 'none' | 'with'

    Возвращает:
      total: int (итого в рублях)
      rows: list of [str, int] (строки детализации)
      text: str (текст для заявки)
    """
    pricing = get_pricing()
    euro_rate = int(pricing.get("euro_rate", 100))

    awning_type = params.get("awning_type", "standard")
    config = params.get("config", "open")
    width = float(params.get("width", 4.0))
    control = params.get("control", "electric")
    installation = params.get("installation", "none")

    base: float = 0
    fabric_cost: float = 0
    frame_cost: float = 0
    control_cost: float = 0
    sensor_cost: float = 0
    light_cost: float = 0
    install_cost: float = 0
    rows: list[list] = []

    if awning_type in ("standard", "storefront"):
        proj = float(params.get("projection", 3.0))
        fabric = params.get("fabric", "gaviota")
        fc = params.get("frame_color", "white")

        if awning_type == "standard":
            sw = next_std(width)
            if config == "open":
                base = get_price(pricing["PRICES_OPEN"], sw, proj)
            elif config == "semi":
                base = get_price(pricing["PRICES_SEMI"], sw, proj)
            else:
                base = get_price(pricing["PRICES_CASSETTE"], sw, proj)
            config_name = _CONFIG_NAMES.get(config, config)
            rows.append([f"Маркиза {config_name} {width}×{proj}м", base * euro_rate])
        else:
            sw = next_std(width)
            if config == "g400":
                base = get_price(pricing["PRICES_G400"], sw, proj)
            else:
                base = get_price(pricing["PRICES_G450"], sw, proj)
            rows.append([f"Витринная маркиза {config.upper()} {width}×{proj}м", base * euro_rate])

        # Доплата за ткань (T-001 fix: используем реальные значения option)
        if fabric in ("elements", "solids"):
            fabric_cost = base * 0.05
            fabric_label = "Sattler Elements" if fabric == "elements" else "Sattler Solids"
            rows.append([f"Доплата ткань {fabric_label} (+5%)", fabric_cost * euro_rate])
        elif fabric in ("lumera", "lumera3d"):
            fabric_cost = base * 0.10
            fabric_label = "Sattler Lumera 3D" if fabric == "lumera3d" else "Sattler Lumera"
            rows.append([f"Доплата ткань {fabric_label} (+10%)", fabric_cost * euro_rate])

        # Доплата за цвет каркаса
        if fc in ("brown", "anthracite"):
            frame_cost = base * 0.05
            rows.append(["Доплата цвет каркаса (+5%)", frame_cost * euro_rate])
        elif fc == "custom":
            frame_cost = base * 0.12
            rows.append(["Доплата нестандартный цвет (+12%)", frame_cost * euro_rate])

        if control == "electric":
            brand = params.get("motor_brand", "decolife")
            if brand == "somfy":
                control_cost = 340
            elif brand == "simu":
                control_cost = 225
            else:
                control_cost = 120
            rows.append([f"Электропривод {_MOTOR_NAMES[brand]} с пультом", control_cost * euro_rate])

            sensor = params.get("sensor_type", "none")
            if sensor == "radio":
                sensor_cost = 120 if brand in ("somfy", "simu") else 90
                rows.append(["Датчик ветровых колебаний", sensor_cost * euro_rate])
            elif sensor == "speed":
                sensor_cost = 325
                rows.append(["Датчик ветра и солнца", sensor_cost * euro_rate])

            if awning_type == "standard" and params.get("lighting_option") == "standard":
                deco = brand == "decolife"
                if proj == 1.5:
                    light_cost = 283 if deco else 333
                elif proj == 2.0:
                    light_cost = 319 if deco else 369
                elif proj == 2.5:
                    light_cost = 331 if deco else 381
                elif proj == 3.0:
                    light_cost = 373 if deco else 423
                else:
                    light_cost = 399 if deco else 449
                rows.append(["LED подсветка встроенная", light_cost * euro_rate])
        else:
            control_cost = 50
            rows.append(["Ручное управление", control_cost * euro_rate])

    else:
        # ZIP
        h = float(params.get("height", 2.0))
        sw = next_std(width)
        sh = next_std(h)
        if config == "zip100":
            base = get_price(pricing["ZIP100"], sw, sh)
        else:
            base = get_price(pricing["ZIP130"], sw, sh)
        rows.append([f"ZIP маркиза {_CONFIG_NAMES[config]} {width}×{h}м", base * euro_rate])

        fc_zip = params.get("frame_color_zip", "white")
        if fc_zip == "custom":
            frame_cost = base * 0.10
            rows.append(["Доплата нестандартный цвет (+10%)", frame_cost * euro_rate])

        if control == "electric":
            brand = params.get("motor_brand", "simu")
            small = (width <= 3.5) and (h <= 4.0)
            if brand == "somfy":
                control_cost = 245 if small else 295
            elif brand == "simu":
                control_cost = 225
            else:
                control_cost = 165
            rows.append([f"Электропривод {_MOTOR_NAMES[brand]} с пультом", control_cost * euro_rate])
        else:
            control_cost = 50
            rows.append(["Ручное управление", control_cost * euro_rate])

    comp_rub = (base + fabric_cost + frame_cost + control_cost + sensor_cost + light_cost) * euro_rate
    delivery = comp_rub * 0.10
    rows.append(["Изготовление и подготовка (10%)", delivery])

    if installation == "with":
        if awning_type == "standard":
            proj = float(params.get("projection", 3.0))
            if config == "cassette":
                install_cost = max(25000, comp_rub * 0.13)
            else:
                install_cost = max(21000, comp_rub * 0.18)
        elif awning_type == "storefront":
            install_cost = max(15000, comp_rub * 0.20)
        else:
            h = float(params.get("height", 2.0))
            install_cost = width * h * 20 * euro_rate
        rows.append(["Установка", install_cost])

    total = round(comp_rub + delivery + install_cost)

    # Округляем все значения строк до целых
    rows_out = [[label, round(val)] for label, val in rows]

    # Текст для заявки
    type_name = _TYPE_NAMES.get(awning_type, awning_type)
    if awning_type == "zip":
        size_line = f"Высота: {params.get('height', 2.0)} м"
    else:
        size_line = f"Вылет: {params.get('projection', 3.0)} м"
    if control == "electric":
        brand = params.get("motor_brand", "decolife")
        ctrl_line = f"Электропривод {_MOTOR_NAMES.get(brand, brand)}"
    else:
        ctrl_line = "Ручное"

    text_lines = [
        "[Расчёт: Маркизы]",
        f"Тип: {type_name}",
        f"Конфигурация: {config}",
        f"Ширина: {width} м",
        size_line,
        f"Управление: {ctrl_line}",
        f"Итого: {total:,} ₽".replace(",", " "),
    ]
    text = "\n".join(text_lines)

    return {"total": total, "rows": rows_out, "text": text}
