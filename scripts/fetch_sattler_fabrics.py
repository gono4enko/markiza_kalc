#!/usr/bin/env python3
"""
Парсинг миниатюр Sattler (акрил) со страницы Decolife — коллекции как в калькуляторе:
  lumera3d, lumera, elements, solids (Elements Solids на сайте).

Источник: https://decolife.pro/products/fabrics/sattler-acrylic-fabrics/

Запуск из корня awning-calculator:
  python3 scripts/fetch_sattler_fabrics.py
  python3 scripts/fetch_sattler_fabrics.py --write
  python3 scripts/sync_fabric_std_thumbs.py   # миниатюры в static/img/fabrics/suntex_thumbs/
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

URL = "https://decolife.pro/products/fabrics/sattler-acrylic-fabrics/"
USER_AGENT = "Mozilla/5.0 (compatible; AwningCalculator/1.0; +https://pergolamarket.ru)"
BASE = "https://decolife.pro"

# Уникальные заголовки блоков в разметке страницы
MARK_L3D_END = "\n                                Lumera:\n"
MARK_LUM_END = "\n                                Elements:\n"
MARK_EL_END = "\n                                Elements Solids:\n"
MARK_SOL_END = "Факты о acrylic Sattler"

RE_IMG = re.compile(
    r'src="(/assets/components/phpthumbof/cache/([A-Za-z0-9.-]+)\.([a-f0-9]+)\.webp)"',
    re.IGNORECASE,
)


def fetch_html() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


def slice_between(html: str, start: int, end_marker: str) -> str:
    j = html.find(end_marker, start)
    if j < 0:
        return html[start:]
    return html[start:j]


def extract_ordered_entries(segment: str) -> list[tuple[str, str]]:
    """(полный путь /assets/..., артикул) — порядок как на сайте, без дублей по артикулу."""
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for m in RE_IMG.finditer(segment):
        path, article, _h = m.group(1), m.group(2), m.group(3)
        # Только реальные артикулы (на странице попадаются служебные картинки без «XXX-…»)
        if "-" not in article:
            continue
        if article in seen:
            continue
        seen.add(article)
        out.append((path, article))
    return out


def parse_all(html: str) -> dict[str, list[tuple[str, str]]]:
    i_l3d = html.find("Lumera 3D:")
    if i_l3d < 0:
        raise ValueError("Не найден блок Lumera 3D")

    seg_l3d = slice_between(html, i_l3d, MARK_L3D_END)
    i_lum = html.find(MARK_L3D_END)
    if i_lum < 0:
        raise ValueError("Не найден блок Lumera")
    i_lum += len(MARK_L3D_END)
    seg_lum = slice_between(html, i_lum, MARK_LUM_END)

    i_el = html.find(MARK_LUM_END)
    if i_el < 0:
        raise ValueError("Не найден блок Elements")
    i_el += len(MARK_LUM_END)
    seg_el = slice_between(html, i_el, MARK_EL_END)

    i_sol = html.find(MARK_EL_END)
    if i_sol < 0:
        raise ValueError("Не найден блок Elements Solids")
    i_sol += len(MARK_EL_END)
    seg_sol = slice_between(html, i_sol, MARK_SOL_END)

    return {
        "lumera3d": extract_ordered_entries(seg_l3d),
        "lumera": extract_ordered_entries(seg_lum),
        "elements": extract_ordered_entries(seg_el),
        "solids": extract_ordered_entries(seg_sol),
    }


def js_lines_for_key(key: str, entries: list[tuple[str, str]]) -> list[str]:
    lines = [f"  {key}: ["]
    for path, article in entries:
        url = BASE + path
        lines.append(f"  '{url}|||{article}',")
    lines.append("  ],")
    return lines


def replace_block(data: str, key: str, new_inner_lines: list[str]) -> str:
    needle = f"  {key}: ["
    start = data.find(needle)
    if start < 0:
        raise ValueError(f"В fabric_std_data.js не найдено: {needle}")
    i = start + len(needle)
    depth = 0
    end = -1
    while i < len(data):
        c = data[i]
        if c == "[":
            depth += 1
        elif c == "]":
            if depth == 0:
                end = i + 1
                if i + 1 < len(data) and data[i + 1] == ",":
                    end = i + 2
                break
            depth -= 1
        i += 1
    if end < 0:
        raise ValueError(f"Не закрыт массив {key}")
    header = f"  /* Sattler {key}: decolife.pro. Обновление: scripts/fetch_sattler_fabrics.py --write */\n"
    new_block = header + "\n".join(new_inner_lines)
    return data[:start] + new_block + data[end:]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="Обновить lumera3d/lumera/elements/solids в fabric_std_data.js")
    args = p.parse_args()

    html = fetch_html()
    groups = parse_all(html)

    if args.write:
        path = Path(__file__).resolve().parent.parent / "static" / "js" / "fabric_std_data.js"
        data = path.read_text(encoding="utf-8")
        for key in ("lumera3d", "lumera", "elements", "solids"):
            inner = js_lines_for_key(key, groups[key])
            data = replace_block(data, key, inner)
        path.write_text(data, encoding="utf-8")
        for key, ent in groups.items():
            print(f"  {key}: {len(ent)}", file=sys.stderr)
        print(f"Записано в {path}", file=sys.stderr)
        return 0

    for key in ("lumera3d", "lumera", "elements", "solids"):
        print(f"// --- {key} ({len(groups[key])}) ---")
        print("\n".join(js_lines_for_key(key, groups[key])))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(e, file=sys.stderr)
        raise SystemExit(1)
