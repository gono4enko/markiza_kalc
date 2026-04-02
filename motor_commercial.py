"""
Тексты для КП и заявок: ключевые особенности автоматики Somfy, Simu, Gaviota.
Ключ API motor_brand «decolife» в интерфейсе клиента отображается как Gaviota (родной привод экосистемы).
"""

from __future__ import annotations

import re
from typing import Any


def _strip_html_bullets(items: list[str]) -> list[str]:
    return [re.sub(r"<[^>]+>", "", x or "").replace("\xa0", " ").strip() for x in items]

# Отображаемое имя бренда в текстах для клиента
_MOTOR_DISPLAY: dict[str, str] = {
    "somfy": "Somfy",
    "simu": "Simu",
    "decolife": "Gaviota",
}

# Заголовок блока в КП / заявке
_MOTOR_HEADLINE: dict[str, str] = {
    "somfy": "Somfy — мировой стандарт солнцезащитной автоматики",
    "simu": "Simu — европейское качество и сбалансированная стоимость",
    "decolife": "Gaviota — согласованный привод под конструкцию маркизы",
}

# Маркеры без HTML (текст заявки, мессенджеры)
_MOTOR_BULLETS_PLAIN: dict[str, tuple[str, ...]] = {
    "somfy": (
        "Франция, лидер отрасли: тихие надёжные трубчатые моторы с большим ресурсом циклов.",
        "Экосистема аксессуаров: радиопульты, приёмники, датчики ветра и солнца, сценарии «умного дома» (в т.ч. TaHoma и др.).",
        "Плавный ход, устойчивость к перепадам температур и влажности на фасаде.",
        "Широкая сервисная сеть и доступность комплектующих по всему миру.",
    ),
    "simu": (
        "Европейский бренд (Франция): проверенное соотношение цены и качества для террасных маркиз.",
        "Радиоуправление и типовая совместимость с датчиками и сценариями комфорта на улице.",
        "Компактные моторы, рассчитанные на регулярные циклы работы солнцезащиты.",
        "Оптимальный выбор при ограниченном бюджете без отказа от электропривода европейского уровня.",
    ),
    "decolife": (
        "Испания, экосистема Gaviota: привод подбирается под нашу конструкцию короба и локтей.",
        "Выгодная стоимость владения при заводской увязке механики и электропривода.",
        "Комплект с пультом для ежедневной эксплуатации на террасе и у витрины.",
        "Акцент на стабильной работе узла без избыточной электроники — надёжность в быту.",
    ),
}

# То же для PDF (допускается разметка ReportLab Paragraph)
_MOTOR_BULLETS_HTML: dict[str, tuple[str, ...]] = {
    "somfy": (
        "<b>Франция, лидер отрасли:</b> тихие надёжные трубчатые моторы с большим ресурсом циклов.",
        "<b>Экосистема аксессуаров:</b> радиопульты, приёмники, датчики ветра и солнца, сценарии «умного дома» "
        "(в т.ч. <b>TaHoma</b> и др.).",
        "<b>Плавный ход,</b> устойчивость к перепадам температур и влажности на фасаде.",
        "<b>Сервис и запчасти</b> доступны по всему миру.",
    ),
    "simu": (
        "<b>Европейский бренд (Франция):</b> проверенное соотношение цены и качества для террасных маркиз.",
        "<b>Радиоуправление</b> и типовая совместимость с датчиками и сценариями комфорта на улице.",
        "<b>Компактные моторы,</b> рассчитанные на регулярные циклы работы солнцезащиты.",
        "<b>Оптимальный выбор</b> при ограниченном бюджете без отказа от электропривода европейского уровня.",
    ),
    "decolife": (
        "<b>Испания, экосистема Gaviota:</b> привод подбирается под конструкцию короба и локтей.",
        "<b>Выгодная стоимость владения</b> при заводской увязке механики и электропривода.",
        "<b>Комплект с пультом</b> для ежедневной эксплуатации на террасе и у витрины.",
        "<b>Стабильная работа узла</b> без избыточной электроники — надёжность в быту.",
    ),
}


def motor_brand_display_name(brand_key: str) -> str:
    return _MOTOR_DISPLAY.get(brand_key, brand_key)


def _motor_fallback_dict(b: str) -> dict[str, Any]:
    return {
        "brand_key": b,
        "display_name": _MOTOR_DISPLAY[b],
        "headline": _MOTOR_HEADLINE[b],
        "bullets_plain": list(_MOTOR_BULLETS_PLAIN[b]),
        "bullets_html": list(_MOTOR_BULLETS_HTML[b]),
        "principle_html": _MOTOR_PRINCIPLE_HTML[b],
        "image_kit": "",
    }


def get_motor_commercial(brand_key: str) -> dict[str, Any]:
    """Данные для API, заявки и КП (учёт kp_content.json)."""
    b = brand_key if brand_key in _MOTOR_BULLETS_PLAIN else "decolife"
    try:
        from kp_content import get_effective_motor_block

        em = get_effective_motor_block(b)
        if not em:
            return _motor_fallback_dict(b)
        bh = list(em.get("bullets_html") or _MOTOR_BULLETS_HTML[b])
        bp = em.get("bullets_plain")
        if bp:
            bullets_plain = list(bp)
        else:
            bullets_plain = _strip_html_bullets(bh)
        return {
            "brand_key": b,
            "display_name": str(em.get("display_name") or _MOTOR_DISPLAY[b]),
            "headline": str(em.get("headline") or _MOTOR_HEADLINE[b]),
            "bullets_plain": bullets_plain,
            "bullets_html": bh,
            "principle_html": str(em.get("principle_html") or _MOTOR_PRINCIPLE_HTML[b]),
            "image_kit": str(em.get("image_kit") or ""),
        }
    except Exception:
        return _motor_fallback_dict(b)


# Модели датчиков под выбранную автоматику (локтевая / витринная; ZIP — датчики не подключаются в калькуляторе)
_SENSOR_MODEL_BY_BRAND: dict[tuple[str, str], str] = {
    ("somfy", "radio"): "Eolis Sensor RTS",
    ("somfy", "speed"): "Eolis 3D WireFree RTS",
    ("simu", "radio"): "SIMU 3D WireFree RTS",
    ("simu", "speed"): "SIMU EOSUN RTS",
    ("decolife", "radio"): "Радиодатчик ветра 3D",
    ("decolife", "speed"): "Солнечно-ветровой датчик, встр. АК",
}

_SENSOR_CATEGORY_TITLE: dict[str, str] = {
    "radio": "Датчик ветровых колебаний",
    "speed": "Датчик ветра и солнца",
}


def _normalize_motor_brand_key(motor_brand: str) -> str:
    b = (motor_brand or "").strip().lower()
    if b not in ("somfy", "simu", "decolife"):
        return "decolife"
    return b


def get_sensor_model(motor_brand: str, sensor_type: str) -> str | None:
    """Артикул/название модели датчика или None."""
    if sensor_type not in ("radio", "speed"):
        return None
    k = _normalize_motor_brand_key(motor_brand)
    try:
        from kp_content import get_effective_sensor_block

        sb = get_effective_sensor_block(k, sensor_type)
        if sb and sb.get("model"):
            return str(sb["model"])
    except Exception:
        pass
    return _SENSOR_MODEL_BY_BRAND.get((k, sensor_type))


def get_sensor_price_row_label(motor_brand: str, sensor_type: str) -> str | None:
    """Строка детализации сметы (как в КП)."""
    m = get_sensor_model(motor_brand, sensor_type)
    if not m:
        return None
    title = _SENSOR_CATEGORY_TITLE.get(sensor_type, "Датчик")
    return f"{title} — {m}"


def get_sensor_application_line(motor_brand: str, sensor_type: str) -> str | None:
    """Одна строка для текста заявки / мессенджеров."""
    m = get_sensor_model(motor_brand, sensor_type)
    if not m:
        return None
    title = _SENSOR_CATEGORY_TITLE.get(sensor_type, "Датчик")
    return f"{title}: {m}"


def get_sensor_pdf_pair(motor_brand: str, sensor_type: str) -> tuple[str, str] | None:
    """(заголовок строки, модель) для таблицы конфигурации в PDF."""
    m = get_sensor_model(motor_brand, sensor_type)
    if not m:
        return None
    title = _SENSOR_CATEGORY_TITLE.get(sensor_type)
    if not title:
        return None
    return (title, m)


# Принцип работы электропривода — для блока КП после эскиза
_MOTOR_PRINCIPLE_HTML: dict[str, str] = {
    "somfy": (
        "<b>Принцип работы:</b> трубчатый электропривод устанавливается внутрь вала маркизы. По сигналу с радиопульта "
        "мотор плавно вращает вал и сматывает или разматывает полотно. Встроенные концевики отключают привод в крайних "
        "положениях «открыто / закрыто», что защищает механику от перегруза."
    ),
    "simu": (
        "<b>Принцип работы:</b> компактный трубчатый мотор в вале маркизы получает команды по радиоканалу (пульт в комплекте). "
        "Вращение вала наматывает или снимает ткань с одинаковой скоростью по всей ширине; электроника ограничивает ход в концевых положениях."
    ),
    "decolife": (
        "<b>Принцип работы:</b> электропривод экосистемы Gaviota согласован с креплением и геометрией вала выбранной серии маркизы. "
        "Управление с пульта — раскрытие и укрытие полотна без ручной тяги; концевое выключение в крайних положениях снижает износ узла."
    ),
}

# Функционал датчиков по паре (бренд автоматики, тип)
_SENSOR_COMMERCIAL_HTML: dict[tuple[str, str], dict[str, Any]] = {
    ("somfy", "radio"): {
        "model": "Eolis Sensor RTS",
        "intro": (
            "<b>Назначение:</b> защита маркизы от порывов ветра по факту колебаний полотна и каркаса."
        ),
        "bullets_html": (
            "Радиосвязь <b>RTS</b> с приводом — без проводов между датчиком и мотором.",
            "Реагирует на <b>ветровые колебания</b> конструкции; при превышении порога отправляет команду <b>свернуть</b> полотно.",
            "Снижает риск поломки локтей и разрыва ткани при шквалах; порог чувствительности настраивается при монтаже.",
        ),
    },
    ("somfy", "speed"): {
        "model": "Eolis 3D WireFree RTS",
        "intro": (
            "<b>Назначение:</b> комфорт (солнце) и защита (ветер) в одном автономном радиодатчике."
        ),
        "bullets_html": (
            "<b>WireFree</b> — питание от встроенных элементов, не требует кабеля питания по фасаду.",
            "Учитывает <b>инсоляцию</b>: может инициировать раскрытие тени при ярком солнце (сценарии настраиваются).",
            "Контролирует <b>ветровую нагрузку</b> (в т.ч. 3D-чувствительность) и инициирует укрытие при опасных порывах.",
            "Радиопротокол <b>RTS</b> — совместим с цепочкой приводов и другими устройствами Somfy.",
        ),
    },
    ("simu", "radio"): {
        "model": "SIMU 3D WireFree RTS",
        "intro": (
            "<b>Назначение:</b> автоматическое укрытие маркизы при сильных колебаниях от ветра."
        ),
        "bullets_html": (
            "Беспроводной датчик с питанием от батарей — <b>без прокладки силовых линий</b> к датчику.",
            "<b>3D-измерение</b> вибраций помогает отличить опасные порывы от лёгкой тряски конструкции.",
            "По радиоканалу <b>RTS</b> отдаёт команду приводу Simu на остановку и сворачивание полотна.",
        ),
    },
    ("simu", "speed"): {
        "model": "SIMU EOSUN RTS",
        "intro": (
            "<b>Назначение:</b> совместное управление сценариями «солнце» и «ветер» для террасы."
        ),
        "bullets_html": (
            "Датчик <b>солнца</b> помогает раскрывать маркизу при яркой погоде для затенения (логика согласуется при настройке).",
            "Контур <b>ветра</b> инициирует сворачивание при усилении ветровой нагрузки.",
            "Радиоинтерфейс <b>RTS</b> — согласование с радиоприводами и пультами линейки Simu.",
        ),
    },
    ("decolife", "radio"): {
        "model": "Радиодатчик ветра 3D",
        "intro": (
            "<b>Назначение:</b> защита инвестиции в маркизу при непогоде."
        ),
        "bullets_html": (
            "Крепится на конструкции с полотном и отслеживает <b>колебания</b> от ветра в нескольких осях (3D).",
            "По радиоканалу передаёт команду на <b>сворачивание</b>, пока нагрузка не достигла критической.",
            "Подбирается под комплект автоматики <b>Gaviota</b> в рамках проекта Comfort House.",
        ),
    },
    ("decolife", "speed"): {
        "model": "Солнечно-ветровой датчик, встр. АК",
        "intro": (
            "<b>Назначение:</b> автоматизация тени на солнце и аварийное укрытие при ветре."
        ),
        "bullets_html": (
            "<b>Встроенный аккумулятор (АК)</b> и солнечный элемент — автономное питание, минимум проводки на фасаде.",
            "Канал <b>солнца</b> участвует в сценариях раскрытия для комфорта на террасе.",
            "Канал <b>ветра</b> отслеживает опасные порывы и инициирует сворачивание полотна.",
            "Согласуется с выбранным приводом и приёмником в комплектации <b>Gaviota</b>.",
        ),
    },
}


def get_motor_principle_html(brand_key: str) -> str:
    return get_motor_commercial(brand_key)["principle_html"]


def get_sensor_commercial_detail(motor_brand: str, sensor_type: str) -> dict[str, Any] | None:
    """Тексты для секции КП «датчик»: model, intro, bullets_html, image."""
    if sensor_type not in ("radio", "speed"):
        return None
    k = _normalize_motor_brand_key(motor_brand)
    base = _SENSOR_COMMERCIAL_HTML.get((k, sensor_type))
    try:
        from kp_content import get_effective_sensor_block

        sb = get_effective_sensor_block(k, sensor_type)
        if sb and base:
            return {
                "model": str(sb.get("model") or base["model"]),
                "intro": str(sb.get("intro") or base["intro"]),
                "bullets_html": list(sb.get("bullets_html") or base["bullets_html"]),
                "image": str(sb.get("image") or ""),
            }
        if sb:
            return {
                "model": str(sb.get("model", "")),
                "intro": str(sb.get("intro", "")),
                "bullets_html": list(sb.get("bullets_html") or []),
                "image": str(sb.get("image") or ""),
            }
    except Exception:
        pass
    if not base:
        return None
    return {
        "model": base["model"],
        "intro": base["intro"],
        "bullets_html": list(base["bullets_html"]),
        "image": "",
    }


def default_kp_structure() -> dict[str, Any]:
    """Полный шаблон для kp_content.json (дефолты до слияния с файлом)."""
    motors: dict[str, Any] = {}
    for b in ("somfy", "simu", "decolife"):
        motors[b] = {
            "display_name": _MOTOR_DISPLAY[b],
            "headline": _MOTOR_HEADLINE[b],
            "principle_html": _MOTOR_PRINCIPLE_HTML[b],
            "bullets_html": list(_MOTOR_BULLETS_HTML[b]),
            "bullets_plain": list(_MOTOR_BULLETS_PLAIN[b]),
            "image_kit": "",
        }
    sensors: dict[str, Any] = {}
    for b in ("somfy", "simu", "decolife"):
        for st in ("radio", "speed"):
            raw = _SENSOR_COMMERCIAL_HTML.get((b, st))
            if raw:
                sensors[f"{b}_{st}"] = {
                    "model": raw["model"],
                    "intro": raw["intro"],
                    "bullets_html": list(raw["bullets_html"]),
                    "image": "",
                }
    return {
        "version": 1,
        "motors": motors,
        "sensors": sensors,
        "pdf_labels": {
            "section_equipment": "ПОДОБРАННАЯ АВТОМАТИКА И УПРАВЛЕНИЕ",
            "section_sensor": "ДАТЧИК — ЗАЩИТА И КОМФОРТ",
            "disclaimer": (
                "Расчёт является предварительным коммерческим предложением. "
                "Итоговая стоимость определяется после замера и согласования проекта с менеджером."
            ),
        },
    }
