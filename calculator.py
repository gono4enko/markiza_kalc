"""
Расчётная логика маркиз — Python-порт calculate() из calculator_awning_v2_16.html.

Исправляет баг T-001: значения fabric используют ключи 'elements', 'lumera',
'solids', 'lumera3d' (соответствуют <option value="..."> в HTML),
а не 'sattler_elements' / 'sattler_lumera' из оригинального багованного JS.
"""

import math
import json
import os
from typing import Any, Callable


def _load_pricing() -> dict[str, Any]:
    """Загружает прайс из JSON-файла относительно этого модуля."""
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "static", "data", "awning_pricing.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_PRICING: dict[str, Any] | None = None
_DECOLIFE_OPEN: dict[str, Any] | None = None
_DECOLIFE_SEMI: dict[str, Any] | None = None
_DECOLIFE_CASSETTE: dict[str, Any] | None = None


def get_pricing() -> dict[str, Any]:
    global _PRICING
    if _PRICING is None:
        _PRICING = _load_pricing()
    return _PRICING


def _load_decolife_open() -> dict[str, Any]:
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "static", "data", "decolife_open_elbow.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_decolife_open() -> dict[str, Any]:
    global _DECOLIFE_OPEN
    if _DECOLIFE_OPEN is None:
        _DECOLIFE_OPEN = _load_decolife_open()
    return _DECOLIFE_OPEN


def _load_decolife_semi() -> dict[str, Any]:
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "static", "data", "decolife_semi_elbow.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_decolife_semi() -> dict[str, Any]:
    global _DECOLIFE_SEMI
    if _DECOLIFE_SEMI is None:
        _DECOLIFE_SEMI = _load_decolife_semi()
    return _DECOLIFE_SEMI


def _load_decolife_cassette() -> dict[str, Any]:
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "static", "data", "decolife_cassette_elbow.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_decolife_cassette() -> dict[str, Any]:
    global _DECOLIFE_CASSETTE
    if _DECOLIFE_CASSETTE is None:
        _DECOLIFE_CASSETTE = _load_decolife_cassette()
    return _DECOLIFE_CASSETTE


def reload_pricing() -> dict[str, Any]:
    global _PRICING, _DECOLIFE_OPEN, _DECOLIFE_SEMI, _DECOLIFE_CASSETTE
    _PRICING = _load_pricing()
    _DECOLIFE_OPEN = None
    _DECOLIFE_SEMI = None
    _DECOLIFE_CASSETTE = None
    return _PRICING


def _fabric_tier_decolife(fabric: str) -> str:
    if fabric in ("elements", "solids"):
        return "sattler_cat2"
    if fabric in ("lumera", "lumera3d"):
        return "sattler_cat3"
    return "gaviota"


def _decolife_width_row(table: dict[str, Any], sw: float) -> dict[str, Any] | None:
    s = str(sw)
    if s in table:
        return table[s]  # type: ignore[return-value]
    s2 = f"{sw:.1f}"
    return table.get(s2)  # type: ignore[return-value]


# От ширины стандарта (м): правило «вылет не больше ширина − 0,5» (избегаем скрещённых локтей).
_DECOLIFE_NO_CROSS_MIN_WIDTH_M = 4.0
_DECOLIFE_NO_CROSS_MARGIN_M = 0.5


def _decolife_pair_in_crossed_arms(sw: float, sp: float, meta: dict[str, Any]) -> bool:
    sw_k, sp_k = f"{sw:.1f}", f"{sp:.1f}"
    for pair in meta.get("crossed_arms") or []:
        if len(pair) >= 2 and str(pair[0]) == sw_k and str(pair[1]) == sp_k:
            return True
    return False


def decolife_cell_avoids_crossed_arms(sw: float, sp: float, meta: dict[str, Any]) -> bool:
    """
    Комплектация без скрещённых локтей: не из списка crossed_arms в JSON,
    вылет строго меньше ширины; при ширине стандарта ≥ 4 м — вылет не больше (ширина − 0,5 м).
    """
    if _decolife_pair_in_crossed_arms(sw, sp, meta):
        return False
    if sp + 1e-9 >= sw:
        return False
    if sw + 1e-9 >= _DECOLIFE_NO_CROSS_MIN_WIDTH_M:
        if sp > sw - _DECOLIFE_NO_CROSS_MARGIN_M + 1e-9:
            return False
    return True


def find_decolife_cell(
    table: dict[str, Any],
    w: float,
    p: float,
    *,
    cell_ok: Callable[[float, float], bool] | None = None,
) -> tuple[float, float, float] | None:
    """Минимальная стандартная ширина ≥ w и вылет ≥ p с ценой; cell_ok — доп. фильтр по (sw, sp)."""
    widths = sorted(float(x) for x in table.keys())
    for sw in widths:
        if sw + 1e-9 < w:
            continue
        row = _decolife_width_row(table, sw)
        if not row:
            continue
        projs = sorted(float(x) for x in row.keys())
        for sp in projs:
            if sp + 1e-9 < p:
                continue
            if cell_ok is not None and not cell_ok(sw, sp):
                continue
            key = str(sp) if str(sp) in row else f"{sp:.1f}"
            val = row.get(key)
            if val is None:
                continue
            return (sw, sp, float(val))
    return None


def pick_decolife_cheapest(
    decolife: dict[str, Any],
    fabric: str,
    w: float,
    p: float,
    *,
    no_match_msg: str,
    product_line: str,
    exclude_model_ids: frozenset[str] | None = None,
) -> dict[str, Any]:
    """
    Для каждой серии — минимальная стандартная ширина и вылет, покрывающие запрос (как в прайсе),
    с фильтром скрещённых локтей; затем минимальная цена EUR среди серий, при равенстве — меньший order.
    """
    tier = _fabric_tier_decolife(fabric)
    models = decolife["models"]
    candidates: list[tuple[float, int, str, float, float, dict[str, Any], str]] = []
    had_any_covering_cell = False
    for mid, meta in models.items():
        if exclude_model_ids and mid in exclude_model_ids:
            continue
        if meta.get("pricing_pending"):
            continue
        tables = meta.get("tables") or {}
        if not tables:
            continue
        tbl = tables.get(tier) or tables.get("gaviota")
        if not tbl:
            continue
        if find_decolife_cell(tbl, w, p) is not None:
            had_any_covering_cell = True
        cell = find_decolife_cell(
            tbl,
            w,
            p,
            cell_ok=lambda sw, sp, m=meta: decolife_cell_avoids_crossed_arms(sw, sp, m),
        )
        if cell:
            sw, sp, price = cell
            candidates.append(
                (price, int(meta.get("order", 99)), mid, sw, sp, meta, tier)
            )
    if not candidates:
        if had_any_covering_cell:
            raise ValueError(
                "Для этих ширины и вылета в прайсе есть размеры, но все они дают комплектацию "
                "со скрещёнными локтями (на ~20 % слабее). Уменьшите вылет или увеличьте ширину: "
                "при стандартной ширине от 4 м оптимально вылет не больше чем на 0,5 м меньше ширины."
            )
        raise ValueError(no_match_msg)
    candidates.sort(key=lambda x: (x[0], x[1]))
    price, _ord, mid, sw, sp, meta, tier_used = candidates[0]
    crossed = _decolife_pair_in_crossed_arms(sw, sp, meta)
    return {
        "model_id": mid,
        "series": meta.get("series", mid),
        "short_label": meta.get("short_label", mid),
        "price_eur": price,
        "std_width": sw,
        "std_projection": sp,
        "tier": tier_used,
        "thumbnail": meta.get("thumbnail", ""),
        "description": meta.get("description", ""),
        "frame_note": meta.get("frame_note", ""),
        "lighting_compatible": bool(meta.get("lighting_compatible", True)),
        "crossed_arms": crossed,
        "pricelist_image": meta.get("pricelist_image", ""),
        "product_line": product_line,
    }


def pick_decolife_open_model(
    decolife: dict[str, Any],
    fabric: str,
    w: float,
    p: float,
    *,
    exclude_model_ids: frozenset[str] | None = None,
    no_match_msg: str | None = None,
) -> dict[str, Any]:
    models = decolife["models"]
    g200 = models.get("g200", {})
    note = (g200.get("pricing_note") or "").strip()
    extra = f" {note}" if note else ""
    default_msg = (
        "Нет ячейки прайса Decolife (G90 / G100 / G300) для этих ширины и вылета. "
        "Для крупных проёмов возможна G200 Classic (до 14×4 м)."
        f"{extra}"
    )
    if no_match_msg is None:
        no_match_msg = default_msg
    return pick_decolife_cheapest(
        decolife,
        fabric,
        w,
        p,
        no_match_msg=no_match_msg,
        product_line="open_elbow",
        exclude_model_ids=exclude_model_ids,
    )


def pick_decolife_semi_model(decolife: dict[str, Any], fabric: str, w: float, p: float) -> dict[str, Any]:
    return pick_decolife_cheapest(
        decolife,
        fabric,
        w,
        p,
        no_match_msg=(
            "Нет ячейки прайса Decolife (G110 / G220) для указанных ширины и вылета полукассетной маркизы."
        ),
        product_line="semi_elbow",
    )


def pick_decolife_cassette_model(decolife: dict[str, Any], fabric: str, w: float, p: float) -> dict[str, Any]:
    return pick_decolife_cheapest(
        decolife,
        fabric,
        w,
        p,
        no_match_msg=(
            "Нет ячейки прайса Decolife (G500 / G600 / G700) для указанных ширины и вылета кассетной маркизы."
        ),
        product_line="cassette_elbow",
    )


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
    "g400": "G400 Italy (открытая, Gaviota)",
    "g450": "G450 Desert (кассетная, Gaviota)",
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

# Локтевая / витринная (Sattler SUN-TEX): подписи серии для детализации и заявок
_STD_FABRIC_MFG = "Sattler SUN-TEX"
_STD_FABRIC_SUNTEX_SERIES: dict[str, str] = {
    "gaviota": "Gaviota",
    "elements": "Sattler Elements",
    "solids": "Sattler Solids",
    "lumera": "Sattler Lumera",
    "lumera3d": "Sattler Lumera 3D",
}


def _gaviota_customer_series_label(catalog_series: str) -> str:
    """Подпись серии для клиента: Gaviota вместо Decolife в текстах детализации и КП."""
    return (catalog_series or "").replace("Decolife", "Gaviota")


def _truthy_json_flag(val: Any) -> bool:
    """Распознаёт true из JSON (bool, int, str)."""
    if val is True:
        return True
    if val in (False, None, "", 0):
        return False
    if isinstance(val, (int, float)):
        return bool(val)
    s = str(val).strip().lower()
    return s in ("1", "true", "yes", "on", "да")


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
      fabric_color_label: str — опционально, артикул/оттенок (в детализации — вместе с производителем и серией)
      fabric_zip: 'veozip'|'soltis' — для zip
      frame_color: для standard — 'white'|'brown'|'anthracite'|'custom'
        (открытая Decolife: при anthracite/custom подбор без G90 — см. прайс G100/G300);
        для storefront (G400/G450) — плюс 'ral9005'|'ral9t08'
      frame_color_zip: 'ral9016'|'ral7024'|'ral9t08'|'ral8028'|'custom' — для zip
      control: 'manual' | 'electric'
      motor_brand: 'somfy' | 'simu' | 'decolife'
      sensor_type: 'none' | 'radio' | 'speed'
      lighting_option: 'none' | 'standard'
      installation: 'none' | 'with'
      storefront_tilt_170: bool — витринная G400/G450: угол наклона до 170° (+15% к базе)
      storefront_valance: 'none' | 'straight' | 'shaped' — волан: нет / прямой (10 €/м ширины) / фигурный (15 €/м)

    Возвращает:
      total: int (итого в рублях)
      rows: list of [str, int] (строки детализации)
      text: str (текст для заявки)
      decolife: опционально — подобранная серия (JSON Decolife; в ответе series_display — подпись Gaviota для клиента)
    """
    pricing = get_pricing()
    euro_rate = int(pricing.get("euro_rate", 100))

    awning_type = params.get("awning_type", "standard")
    config = params.get("config", "open")
    width = float(params.get("width", 4.0))
    control = params.get("control", "electric")
    installation = params.get("installation", "none")

    # Автоматическое переключение ZIP 100 → ZIP 130 при превышении лимитов
    if awning_type == "zip" and config == "zip100":
        h_check = float(params.get("height", 2.0))
        if width > 4.0 or h_check > 3.5:
            config = "zip130"
            params = dict(params)  # не мутируем оригинал
            params["config"] = "zip130"

    base: float = 0
    fabric_cost: float = 0
    frame_cost: float = 0
    control_cost: float = 0
    sensor_cost: float = 0
    light_cost: float = 0
    tilt_storefront_eur: float = 0
    valance_storefront_eur: float = 0
    install_cost: float = 0
    rows: list[list] = []
    decolife_pick: dict[str, Any] | None = None

    if awning_type in ("standard", "storefront"):
        proj = float(params.get("projection", 3.0))
        fabric = params.get("fabric", "gaviota")
        fc = params.get("frame_color", "white")

        if awning_type == "standard":
            if config == "open" and pricing.get("use_decolife_open_elbow", True):
                # G90: только RAL 9016 (0%) и RAL 8014 глянец (+5%); антрацит и спец. RAL — подбор G100/G200/G300
                exclude_g90: frozenset[str] | None = (
                    frozenset({"g90"}) if fc in ("anthracite", "custom") else None
                )
                no_open_msg: str | None = None
                if exclude_g90:
                    no_open_msg = (
                        "Для антрацита (RAL 7016) или специального RAL каркаса серия G90 недоступна; "
                        "для ваших ширины и вылета нет подходящей ячейки в G100 / G300. "
                        "Измените размеры или выберите RAL 9016 глянец белый / RAL 8014 коричневый."
                    )
                decolife_pick = pick_decolife_open_model(
                    get_decolife_open(),
                    fabric,
                    width,
                    proj,
                    exclude_model_ids=exclude_g90,
                    no_match_msg=no_open_msg,
                )
                base = decolife_pick["price_eur"]
                std_w = decolife_pick["std_width"]
                std_p = decolife_pick["std_projection"]
                x_lbl = " · скрещенные локти" if decolife_pick.get("crossed_arms") else ""
                rows.append(
                    [
                        f"{_gaviota_customer_series_label(decolife_pick['series'])}, стандарт {std_w:g}×{std_p:g} м{x_lbl}",
                        base * euro_rate,
                    ]
                )
            elif config == "semi" and pricing.get("use_decolife_semi_elbow", True):
                decolife_pick = pick_decolife_semi_model(get_decolife_semi(), fabric, width, proj)
                base = decolife_pick["price_eur"]
                std_w = decolife_pick["std_width"]
                std_p = decolife_pick["std_projection"]
                x_lbl = " · скрещенные локти" if decolife_pick.get("crossed_arms") else ""
                rows.append(
                    [
                        f"{_gaviota_customer_series_label(decolife_pick['series'])}, стандарт {std_w:g}×{std_p:g} м{x_lbl}",
                        base * euro_rate,
                    ]
                )
            elif config == "cassette" and pricing.get("use_decolife_cassette_elbow", True):
                decolife_pick = pick_decolife_cassette_model(get_decolife_cassette(), fabric, width, proj)
                base = decolife_pick["price_eur"]
                std_w = decolife_pick["std_width"]
                std_p = decolife_pick["std_projection"]
                x_lbl = " · скрещенные локти" if decolife_pick.get("crossed_arms") else ""
                rows.append(
                    [
                        f"{_gaviota_customer_series_label(decolife_pick['series'])}, стандарт {std_w:g}×{std_p:g} м{x_lbl}",
                        base * euro_rate,
                    ]
                )
            else:
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
            rows.append([f"Витринная маркиза {_CONFIG_NAMES[config]} {width}×{proj}м", base * euro_rate])
            if config in ("g400", "g450") and _truthy_json_flag(params.get("storefront_tilt_170")):
                tilt_storefront_eur = base * 0.15
                rows.append(
                    ["Изменение угла наклона до 170° (+15% к базе)", tilt_storefront_eur * euro_rate]
                )
            _val = str(params.get("storefront_valance", "none") or "none").strip().lower()
            if config in ("g400", "g450") and _val == "straight":
                valance_storefront_eur = width * 10.0
                rows.append(
                    [
                        f"Волан прямой ({width:g} м × 10 €/м ширины)",
                        valance_storefront_eur * euro_rate,
                    ]
                )
            elif config in ("g400", "g450") and _val == "shaped":
                valance_storefront_eur = width * 15.0
                rows.append(
                    [
                        f"Волан фигурный ({width:g} м × 15 €/м ширины)",
                        valance_storefront_eur * euro_rate,
                    ]
                )

        # Доплата за ткань — только если база не из матрицы Decolife (там уже категория ткани)
        if decolife_pick is None:
            if fabric in ("elements", "solids"):
                fabric_cost = base * 0.05
                fabric_label = "Sattler Elements" if fabric == "elements" else "Sattler Solids"
                rows.append([f"Доплата ткань {fabric_label} (+5%)", fabric_cost * euro_rate])
            elif fabric in ("lumera", "lumera3d"):
                fabric_cost = base * 0.10
                fabric_label = "Sattler Lumera 3D" if fabric == "lumera3d" else "Sattler Lumera"
                rows.append([f"Доплата ткань {fabric_label} (+10%)", fabric_cost * euro_rate])

        swatch_lbl = (params.get("fabric_color_label") or params.get("fabric_swatch_label") or "").strip()
        if swatch_lbl:
            series = _STD_FABRIC_SUNTEX_SERIES.get(fabric, fabric)
            rows.append(
                [
                    f"Оттенок ткани: {_STD_FABRIC_MFG} · серия «{series}» · арт. {swatch_lbl}",
                    0,
                ]
            )

        # Доплата за цвет каркаса (локтевая vs витринная G400/G450 — разные прайсы)
        if awning_type == "storefront":
            if fc in ("white", "brown", "ral9005"):
                pass
            elif fc in ("anthracite", "ral9t08"):
                frame_cost = base * 0.10
                rows.append(["Доплата цвет каркаса RAL 7016 / 9T08 (+10%)", frame_cost * euro_rate])
            elif fc == "custom":
                frame_cost = base * 0.12
                rows.append(["Доплата нестандартный цвет (+12%)", frame_cost * euro_rate])
        else:
            open_deco = (
                decolife_pick is not None
                and decolife_pick.get("product_line") == "open_elbow"
            )
            if open_deco and decolife_pick.get("model_id") == "g90":
                if fc == "brown":
                    frame_cost = base * 0.05
                    rows.append(
                        ["Доплата RAL 8014 глянец коричневый (+5%)", frame_cost * euro_rate]
                    )
            elif open_deco:
                # G100 / G200 / G300: как в прайсе Gaviota (RAL 9016 — 0%; остальное — наценки)
                if fc == "brown":
                    frame_cost = base * 0.05
                    rows.append(
                        [
                            "Доплата RAL 8014 глянец или муар текстур. коричневый (+5%)",
                            frame_cost * euro_rate,
                        ]
                    )
                elif fc == "anthracite":
                    frame_cost = base * 0.05
                    rows.append(
                        [
                            "Доплата RAL 7016 муар текстур. антрацит (+5%)",
                            frame_cost * euro_rate,
                        ]
                    )
                elif fc == "custom":
                    frame_cost = base * 0.12
                    rows.append(["Доплата специальный RAL (+12%)", frame_cost * euro_rate])
            elif (
                decolife_pick is not None
                and decolife_pick.get("product_line") == "semi_elbow"
                and decolife_pick.get("model_id") in ("g110", "g220")
            ):
                # G110 / G220: RAL 9016 — 0%; 8014 глянец/муар коричн. — +5%; 7016 — +5%; спец. RAL — +12%
                if fc == "brown":
                    frame_cost = base * 0.05
                    rows.append(
                        [
                            "Доплата RAL 8014 глянец или муар текстур. коричневый (+5%)",
                            frame_cost * euro_rate,
                        ]
                    )
                elif fc == "anthracite":
                    frame_cost = base * 0.05
                    rows.append(
                        [
                            "Доплата RAL 7016 муар текстур. антрацит (+5%)",
                            frame_cost * euro_rate,
                        ]
                    )
                elif fc == "custom":
                    frame_cost = base * 0.12
                    rows.append(["Доплата специальный RAL (+12%)", frame_cost * euro_rate])
            elif (
                decolife_pick is not None
                and decolife_pick.get("product_line") == "cassette_elbow"
                and decolife_pick.get("model_id") in ("g500", "g600", "g700")
            ):
                # G500 / G600 / G700: RAL 9016 — 0%; 8014 — +5%; 7016 — +5%; спец. RAL — +12%
                if fc == "brown":
                    frame_cost = base * 0.05
                    rows.append(
                        [
                            "Доплата RAL 8014 глянец или муар текстур. коричневый (+5%)",
                            frame_cost * euro_rate,
                        ]
                    )
                elif fc == "anthracite":
                    frame_cost = base * 0.05
                    rows.append(
                        [
                            "Доплата RAL 7016 муар текстур. антрацит (+5%)",
                            frame_cost * euro_rate,
                        ]
                    )
                elif fc == "custom":
                    frame_cost = base * 0.12
                    rows.append(["Доплата специальный RAL (+12%)", frame_cost * euro_rate])
            elif fc in ("brown", "anthracite"):
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
                if (
                    decolife_pick
                    and decolife_pick.get("product_line") == "open_elbow"
                    and not decolife_pick.get("lighting_compatible", True)
                ):
                    rows.append(["LED-подсветка: серия G300 Smart не интегрируется со встроенным освещением", 0])
                else:
                    deco = brand == "decolife"
                    lp = float(decolife_pick["std_projection"]) if decolife_pick else proj
                    if lp <= 1.5 + 1e-9:
                        light_cost = 283 if deco else 333
                    elif lp <= 2.0 + 1e-9:
                        light_cost = 319 if deco else 369
                    elif lp <= 2.5 + 1e-9:
                        light_cost = 331 if deco else 381
                    elif lp <= 3.0 + 1e-9:
                        light_cost = 373 if deco else 423
                    elif lp <= 3.5 + 1e-9:
                        light_cost = 399 if deco else 449
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

        # Ткань ZIP с артикулом цвета
        _ZIP_FABRIC_NAMES = {
            "veozip": "Screen Veosol / Veozip",
            "soltis": "Screen Soltis 86/92",
            "copaco": "Screen Copaco",
        }
        _ZIP_FABRIC_MFG = {
            "veozip": "Serge Ferrari",
            "soltis": "Serge Ferrari",
            "copaco": "Copaco Screenweavers",
        }
        fz = params.get("fabric_zip", "veozip")
        fabric_label = _ZIP_FABRIC_NAMES.get(fz, fz)
        mfg_zip = _ZIP_FABRIC_MFG.get(fz)
        if mfg_zip:
            fabric_label = f"{mfg_zip} · {fabric_label}"
        color_art = (params.get("veozip_color") or
                     params.get("soltis_color") or
                     params.get("copaco_color") or "")
        col_name = (params.get("soltis_collection") or
                    params.get("copaco_collection") or "")
        if col_name:
            fabric_label += f" {col_name}"
        if color_art:
            fabric_label += f" · арт. {color_art}"
        rows.append([f"Ткань: {fabric_label}", 0])

        _ZIP_COLOR_NAMES = {
            "ral9016": "RAL 9016 матовый белый",
            "ral7024": "RAL 7024 матовый серый",
            "ral9t08": "RAL 9T08 текстурированный графит",
            "ral8028": "RAL 8028 муар коричневый",
            "custom":  "Специальный RAL",
        }
        fc_zip = params.get("frame_color_zip", "ral9016")
        color_name = _ZIP_COLOR_NAMES.get(fc_zip, fc_zip)
        if fc_zip == "custom":
            frame_cost = base * 0.10
            rows.append([f"Цвет каркаса: {color_name} (+10%)", frame_cost * euro_rate])
        else:
            rows.append([f"Цвет каркаса: {color_name}", 0])

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

    comp_rub = (
        base
        + fabric_cost
        + frame_cost
        + control_cost
        + sensor_cost
        + light_cost
        + tilt_storefront_eur
        + valance_storefront_eur
    ) * euro_rate
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
    if decolife_pick:
        text_lines.insert(
            3,
            f"Серия: {_gaviota_customer_series_label(decolife_pick['series'])} (стандарт {decolife_pick['std_width']:g}×{decolife_pick['std_projection']:.1f} м)",
        )
    if awning_type == "standard":
        text_lines.insert(
            -1,
            "Локти: серия и сечение подбираются под вылет (ориентир Smart / Premium plus / LED Concept / Arko) — детали в КП.",
        )
    if awning_type == "storefront" and tilt_storefront_eur > 0:
        text_lines.insert(-1, "Опция: угол наклона до 170° (+15% к базе витринной маркизы)")
    if awning_type == "storefront" and valance_storefront_eur > 0:
        _vln = str(params.get("storefront_valance", "none") or "none").strip().lower()
        if _vln == "straight":
            text_lines.insert(
                -1,
                f"Опция: волан прямой — {width:g} м ширины × 10 €/м",
            )
        elif _vln == "shaped":
            text_lines.insert(
                -1,
                f"Опция: волан фигурный — {width:g} м ширины × 15 €/м",
            )
    text = "\n".join(text_lines)

    out: dict[str, Any] = {"total": total, "rows": rows_out, "text": text}
    if decolife_pick:
        out["decolife"] = {
            "model_id": decolife_pick["model_id"],
            "series": decolife_pick["series"],
            "series_display": _gaviota_customer_series_label(decolife_pick["series"]),
            "short_label": decolife_pick["short_label"],
            "std_width": decolife_pick["std_width"],
            "std_projection": decolife_pick["std_projection"],
            "crossed_arms": decolife_pick["crossed_arms"],
            "thumbnail": decolife_pick["thumbnail"],
            "description": decolife_pick["description"],
            "frame_note": decolife_pick.get("frame_note", ""),
            "pricelist_image": decolife_pick.get("pricelist_image", ""),
            "lighting_compatible": decolife_pick.get("lighting_compatible", True),
            "product_line": decolife_pick.get("product_line", "open_elbow"),
        }
    return out
