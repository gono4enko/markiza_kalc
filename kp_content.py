"""
Настройки текстов и медиа для КП (коммерческого предложения).
Файл static/data/kp_content.json накладывается поверх встроенных значений из motor_commercial.default_kp_structure().
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any

_BASE = os.path.dirname(os.path.abspath(__file__))
_KP_JSON = os.path.join(_BASE, "static", "data", "kp_content.json")

_raw_cache: dict[str, Any] | None = None


def _deep_merge(base: Any, over: Any) -> Any:
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            if k in out and isinstance(out[k], dict) and isinstance(v, dict):
                out[k] = _deep_merge(out[k], v)
            else:
                out[k] = copy.deepcopy(v)
        return out
    return copy.deepcopy(over if over is not None else base)


def _load_raw_file() -> dict[str, Any]:
    if not os.path.isfile(_KP_JSON):
        return {}
    try:
        with open(_KP_JSON, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def reload_kp_content() -> None:
    global _raw_cache
    _raw_cache = None


def get_kp_raw() -> dict[str, Any]:
    """Только содержимое JSON (без слияния с дефолтами)."""
    global _raw_cache
    if _raw_cache is None:
        _raw_cache = _load_raw_file()
    return _raw_cache


def get_kp_merged() -> dict[str, Any]:
    """Полная эффективная конфигурация КП для рантайма и предпросмотра в админке."""
    import motor_commercial as mc

    base = mc.default_kp_structure()
    return _deep_merge(base, get_kp_raw())


def get_effective_motor_block(brand: str) -> dict[str, Any]:
    m = get_kp_merged().get("motors", {})
    return m.get(brand, m.get("decolife", {}))


def get_effective_sensor_block(brand: str, sensor_type: str) -> dict[str, Any] | None:
    if sensor_type not in ("radio", "speed"):
        return None
    b = brand if brand in ("somfy", "simu", "decolife") else "decolife"
    key = f"{b}_{sensor_type}"
    sensors = get_kp_merged().get("sensors", {})
    return sensors.get(key)


def get_pdf_label(key: str, default: str = "") -> str:
    labels = get_kp_merged().get("pdf_labels", {})
    v = labels.get(key)
    return str(v).strip() if v else default


def save_kp_content(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_KP_JSON), exist_ok=True)
    with open(_KP_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    reload_kp_content()
