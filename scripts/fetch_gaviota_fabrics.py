#!/usr/bin/env python3
"""
Парсинг миниатюр Gaviota со страницы Decolife.
Выводит блок `gaviota: [ ... ]` для вставки в static/js/fabric_std_data.js

Источник: https://decolife.pro/products/fabrics/gaviota-acrylic-fabrics/

Запуск из корня awning-calculator:
  python3 scripts/fetch_gaviota_fabrics.py
  python3 scripts/fetch_gaviota_fabrics.py --write  # перезаписать gaviota в fabric_std_data.js
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

URL = "https://decolife.pro/products/fabrics/gaviota-acrylic-fabrics/"
USER_AGENT = "Mozilla/5.0 (compatible; AwningCalculator/1.0; +https://pergolamarket.ru)"

RE_THUMB = re.compile(
    r"/assets/components/phpthumbof/cache/(80180\d+)\.([a-f0-9]+)\.webp"
)


def fetch_html() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_entries(html: str) -> list[tuple[str, str]]:
    """Порядок как на странице: (артикул, hash phpthumbof)."""
    order: list[str] = []
    hashes: dict[str, str] = {}
    for m in RE_THUMB.finditer(html):
        art, h = m.group(1), m.group(2)
        if art not in hashes:
            hashes[art] = h
            order.append(art)
    return [(art, hashes[art]) for art in order]


def lines_for_js(entries: list[tuple[str, str]]) -> list[str]:
    base = "https://decolife.pro/assets/components/phpthumbof/cache"
    out = ["  gaviota: ["]
    for art, h in entries:
        url = f"{base}/{art}.{h}.webp"
        out.append(f"  '{url}|||{art}',")
    out.append("  ],")
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--write",
        action="store_true",
        help="Заменить массив gaviota в static/js/fabric_std_data.js",
    )
    args = p.parse_args()

    html = fetch_html()
    entries = parse_entries(html)
    if not entries:
        print("Не найдено миниатюр phpthumbof — разметка сайта могла измениться.", file=sys.stderr)
        return 1

    js_lines = lines_for_js(entries)
    text = "\n".join(js_lines)

    if not args.write:
        print(text)
        print(f"\n# Всего: {len(entries)}", file=sys.stderr)
        return 0

    path = Path(__file__).resolve().parent.parent / "static" / "js" / "fabric_std_data.js"
    data = path.read_text(encoding="utf-8")
    start = data.find("  gaviota: [")
    if start < 0:
        print("В fabric_std_data.js не найден блок gaviota: [", file=sys.stderr)
        return 1
    depth = 0
    i = start + len("  gaviota: [")
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
        print("Не удалось найти конец массива gaviota", file=sys.stderr)
        return 1

    new_block = "  /* Gaviota: миниатюры с decolife.pro. Обновление: scripts/fetch_gaviota_fabrics.py --write */\n" + text
    updated = data[:start] + new_block + data[end:]
    path.write_text(updated, encoding="utf-8")
    print(f"Записано {len(entries)} позиций в {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
