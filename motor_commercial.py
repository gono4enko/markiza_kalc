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
    "somfy": "Somfy — бесшумное открытие одним касанием, 50 лет в лидерах отрасли",
    "simu": "Simu — европейская надёжность без переплаты за известный бренд",
    "decolife": "Gaviota — родной привод маркизы: механика и мотор созданы друг для друга",
}

# Маркеры без HTML (текст заявки, мессенджеры)
_MOTOR_BULLETS_PLAIN: dict[str, tuple[str, ...]] = {
    "somfy": (
        "Не слышно совсем. Мотор Somfy работает бесшумно — никакого жужжания рядом с зоной отдыха.",
        "Управляй голосом или по расписанию: Алиса, Google Home, Apple HomeKit, TaHoma.",
        "50 лет на рынке, сервис везде: Somfy обслуживается по всей России.",
        "Работает в российском климате: рассчитан на перепады от −20°C до +60°C.",
    ),
    "simu": (
        "Европейское качество по честной цене — французское производство без наценки за маркетинг.",
        "Пульт уже в комплекте: никаких проводов по фасаду, радиоуправление сразу из коробки.",
        "Рассчитан на ежедневную работу — мотор для многолетних циклов на открытой террасе.",
        "Правильный выбор, когда нужна надёжная европейская электрика без переплаты за бренд.",
    ),
    "decolife": (
        "Маркиза и мотор — одна система Gaviota (Испания, с 1973 г.): привод подогнан под вал и короб модели.",
        "Открытие одной кнопкой — пульт в комплекте. Утром кофе на террасе без возни с тягой.",
        "Надёжность без излишеств: минимум электроники = минимум поломок.",
        "Автоматически убирается при ветре (при наличии датчика) — маркиза сворачивается сама.",
    ),
}

# То же для PDF (допускается разметка ReportLab Paragraph)
_MOTOR_BULLETS_HTML: dict[str, tuple[str, ...]] = {
    "somfy": (
        "<b>Не слышно совсем.</b> Мотор Somfy работает бесшумно — никакого жужжания рядом с зоной отдыха.",
        "<b>Управляй голосом или по расписанию:</b> совместим с умным домом — Алиса, Google Home, Apple HomeKit, TaHoma. "
        "Маркиза открывается сама в нужное время.",
        "<b>50 лет на рынке, сервис везде:</b> Somfy обслуживается по всей России. Запчасти и мастера найдутся через 10 лет.",
        "<b>Работает в российском климате:</b> рассчитан на перепады от −20°C до +60°C, устойчив к влажности.",
    ),
    "simu": (
        "<b>Европейское качество по честной цене</b> — французское производство без наценки за маркетинг.",
        "<b>Пульт уже в комплекте:</b> никаких проводов по фасаду, радиоуправление сразу из коробки.",
        "<b>Рассчитан на ежедневную работу:</b> мотор для многолетних циклов открытия и закрытия.",
        "<b>Правильный выбор,</b> когда нужна надёжная европейская электрика без переплаты за бренд.",
    ),
    "decolife": (
        "<b>Маркиза и мотор — одна система Gaviota (Испания, с 1973 г.):</b> привод подогнан под вал и короб вашей модели.",
        "<b>Открытие одной кнопкой</b> — пульт входит в комплект. Утром кофе на террасе без возни с ручной тягой.",
        "<b>Надёжность без излишеств:</b> минимум электроники = минимум поломок. Концевики защищают механику.",
        "<b>Автоматически убирается при ветре</b> (при наличии датчика) — маркиза сворачивается сама.",
    ),
}

# Короткий сценарий для веба и единообразия с КП
_MOTOR_SCENARIO: dict[str, str] = {
    "somfy": (
        "Просыпаетесь — маркиза уже открылась по расписанию. "
        "В полдень датчик закрыл её сам. Вечером сказали «Алиса, закрой маркизу» — готово. "
        "Это не фантастика, это Somfy с TaHoma."
    ),
    "simu": (
        "Нажали кнопку на пульте — маркиза открылась. Нажали ещё раз — закрылась. "
        "Никаких приложений, никаких настроек. Просто работает каждый день."
    ),
    "decolife": (
        "Утренний кофе без слепящего солнца. Обед на террасе в июльский полдень. "
        "Ужин под открытым небом — маркиза свернулась сама, когда поднялся ветер. "
        "Вы даже не заметили. Это и есть правильно настроенная терраса."
    ),
}

# Сценарии для витринной маркизы (веб/заявки; в API отдаётся при необходимости отдельно)
_STOREFRONT_SCENARIO: dict[str, str] = {
    "somfy": (
        "9 утра: маркиза открылась по расписанию. Блики с витрины исчезли — "
        "покупатели снова видят товары. Всё без участия персонала."
    ),
    "simu": (
        "Нажали кнопку — маркиза опустилась перед витриной. "
        "Блики пропали, витрина работает. Нажали ещё раз вечером — убралась."
    ),
    "decolife": (
        "Солнце бьёт в витрину — товары не видны, покупатели проходят мимо. "
        "Маркиза открылась в 9 утра: блики исчезли, витрина снова продаёт."
    ),
}


def get_storefront_scenario(brand_key: str) -> str:
    """Короткий сценарий под бренд привода для витринной маркизы."""
    b = brand_key if brand_key in _STOREFRONT_SCENARIO else "decolife"
    return _STOREFRONT_SCENARIO.get(b, "")


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
        "scenario": _MOTOR_SCENARIO.get(b, ""),
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
            "scenario": str(em.get("scenario") or _MOTOR_SCENARIO.get(b, "")),
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
        "<b>Как это выглядит в жизни:</b> вы просыпаетесь — маркиза уже открылась по расписанию. "
        "В полдень датчик солнца закрыл её сам. Вечером — одно касание пульта или команда голосом. "
        "Маркиза стала частью распорядка дня, о которой не нужно думать. "
        "<b>Как это работает:</b> трубчатый электропривод встроен в вал маркизы. По радиосигналу "
        "мотор плавно вращает вал и сматывает или разматывает полотно. Встроенные концевики "
        "отключают привод в крайних положениях и защищают механику от перегруза."
    ),
    "simu": (
        "<b>Как это выглядит в жизни:</b> нажали кнопку — маркиза открылась. "
        "Нажали ещё раз — закрылась. Никаких приложений, никаких настроек. "
        "Просто работает каждый день, без сюрпризов. "
        "<b>Как это работает:</b> компактный трубчатый мотор в вале маркизы получает команды "
        "по радиоканалу. Вращение вала сматывает или разматывает ткань с одинаковым натяжением "
        "по всей ширине; электроника ограничивает ход в концевых положениях."
    ),
    "decolife": (
        "<b>Как это выглядит в жизни:</b> утренний кофе без слепящего солнца. "
        "Обед на террасе в июльский полдень. Ужин под открытым небом — "
        "маркиза свернулась сама, когда поднялся ветер. Вы даже не заметили. "
        "<b>Как это работает:</b> электропривод экосистемы Gaviota согласован с креплением "
        "и геометрией вала вашей модели маркизы. Управление с пульта — раскрытие и укрытие "
        "полотна без ручной тяги; концевики в крайних положениях снижают износ узла."
    ),
}

# Функционал датчиков по паре (бренд автоматики, тип)
# Картинки для секции КП «датчик» (если не заданы в kp_content.json)
_DEFAULT_SENSOR_IMAGE_BY_TYPE: dict[str, str] = {
    "radio": "/static/img/somfy_wind_vibration_sensor.png",
    "speed": "/static/img/sensor_wind_sun.png",
}


def _sensor_detail_fill_default_image(d: dict[str, Any], sensor_type: str) -> dict[str, Any]:
    out = dict(d)
    if not str(out.get("image") or "").strip():
        out["image"] = _DEFAULT_SENSOR_IMAGE_BY_TYPE.get(sensor_type, "")
    return out


_SENSOR_COMMERCIAL_HTML: dict[tuple[str, str], dict[str, Any]] = {
    ("somfy", "radio"): {
        "model": "Eolis Sensor RTS",
        "intro": (
            "<b>Защита вашей инвестиции:</b> маркиза без датчика — это риск каждый раз, "
            "когда уходите из дома при раскрытом полотне. Один шквал — погнутые локти, "
            "разорванная ткань, ремонт на несколько недель. Eolis Sensor RTS работает "
            "по радиоканалу без проводов и окупается при первой же непогоде."
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
            "<b>Умный дом для вашей террасы:</b> датчик сам открывает тень при ярком солнце "
            "и убирает маркизу до того, как налетит шквал — даже когда вас нет дома. "
            "Питание от батареек, никаких кабелей по фасаду."
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
            "<b>Маркиза убирается сама, когда нужно:</b> датчик определяет опасные колебания "
            "от ветра и отправляет команду на сворачивание до того, как нагрузка стала критической. "
            "Работает без проводов и без вашего участия."
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
            "<b>Тень сама — защита сама:</b> датчик открывает маркизу при ярком солнце "
            "и убирает её при усилении ветра. Всё автоматически, по радиоканалу."
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
            "<b>Что будет без датчика:</b> один шквальный порыв при раскрытом полотне — "
            "локти погнуты, ткань разорвана. Ремонт от 15 000 руб., ждать 2–3 недели. "
            "Датчик стоит в разы дешевле и окупается при первой же непогоде."
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
            "<b>Автопилот для вашей террасы:</b> датчик сам открывает маркизу в жару "
            "и убирает её при ветре — даже когда вас нет дома. "
            "Встроенный аккумулятор: никаких кабелей по фасаду."
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
            return _sensor_detail_fill_default_image(
                {
                    "model": str(sb.get("model") or base["model"]),
                    "intro": str(sb.get("intro") or base["intro"]),
                    "bullets_html": list(sb.get("bullets_html") or base["bullets_html"]),
                    "image": str(sb.get("image") or ""),
                },
                sensor_type,
            )
        if sb:
            return _sensor_detail_fill_default_image(
                {
                    "model": str(sb.get("model", "")),
                    "intro": str(sb.get("intro", "")),
                    "bullets_html": list(sb.get("bullets_html") or []),
                    "image": str(sb.get("image") or ""),
                },
                sensor_type,
            )
    except Exception:
        pass
    if not base:
        return None
    return _sensor_detail_fill_default_image(
        {
            "model": base["model"],
            "intro": base["intro"],
            "bullets_html": list(base["bullets_html"]),
            "image": "",
        },
        sensor_type,
    )


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
            "scenario": _MOTOR_SCENARIO.get(b, ""),
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
            "section_led": "LED-ПОДСВЕТКА В ЛОКТЯХ (CONCEPT LED)",
            "disclaimer": (
                "Расчёт предварительный. Цена фиксируется в договоре после замера — "
                "никаких скрытых доплат после подписания."
            ),
        },
    }
