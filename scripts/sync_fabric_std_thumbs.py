#!/usr/bin/env python3
"""
Однократная (или периодическая) загрузка миниатюр SUN-TEX из fabric_std_data.js на диск
и замена URL в JS на /static/img/fabrics/suntex_thumbs/{бренд}/{артикул}.webp

После обновления каталога через fetch_gaviota_fabrics.py / fetch_sattler_fabrics.py --write
запустите этот скрипт, чтобы PDF и сайт не ходили на decolife.pro.

Из корня awning-calculator:
  python3 scripts/sync_fabric_std_thumbs.py
  python3 scripts/sync_fabric_std_thumbs.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (compatible; AwningCalculator/1.1; +https://pergolamarket.ru)"
RE_LINE = re.compile(r"'(https://decolife\.pro[^']+)\|\|\|([^']+)'")
RE_BRAND = re.compile(r"^\s*([a-z0-9]+)\s*:\s*\[")


def safe_article(label: str) -> str:
    s = (label or "").strip()
    s = re.sub(r"[^\w.\-]+", "_", s)
    return s[:180] or "unknown"


def download(url: str, dest: Path, retries: int = 4) -> None:
    """Сначала curl (стабильнее TLS в некоторых окружениях), иначе urllib с повторами."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("curl"):
        r = subprocess.run(
            [
                "curl", "-sfL", "--max-time", "90",
                "-A", USER_AGENT,
                "-o", str(dest),
                url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode == 0 and dest.is_file():
            sz = dest.stat().st_size
            if 80 < sz < 6_000_000:
                return

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=75) as resp:
                data = resp.read()
            if not data or len(data) > 6_000_000:
                raise ValueError("пустой или слишком большой ответ")
            dest.write_bytes(data)
            return
        except (urllib.error.URLError, OSError, ValueError) as e:
            last_err = e
            time.sleep(1.2 * (attempt + 1))
    assert last_err is not None
    raise last_err


def process_js(path: Path, out_root: Path, dry_run: bool, skip_existing: bool) -> int:
    text = path.read_text(encoding="utf-8")
    brand: str | None = None
    lines_out: list[str] = []
    errors = 0
    ok = 0

    for line in text.splitlines(keepends=True):
        bare = line.rstrip("\n\r")
        m_br = RE_BRAND.match(bare)
        if m_br:
            brand = m_br.group(1)
        m = RE_LINE.search(bare)
        if not m or not brand:
            lines_out.append(line)
            continue
        url, label = m.group(1), m.group(2)
        safe = safe_article(label)
        rel = f"img/fabrics/suntex_thumbs/{brand}/{safe}.webp"
        dest = out_root / rel
        web_path = f"/static/{rel}"

        if not dry_run:
            try:
                if skip_existing and dest.is_file():
                    pass
                else:
                    download(url, dest)
                    time.sleep(0.2)  # не ддосить источник
            except (urllib.error.URLError, OSError, ValueError) as e:
                print(f"[err] {brand} {label}: {e}", file=sys.stderr)
                errors += 1
                lines_out.append(line)
                continue

        # заменить только URL между первой кавычкой и |||
        new_bare = bare[: m.start(1)] + web_path + bare[m.end(1) :]
        lines_out.append(new_bare + ("\n" if line.endswith("\n") else ""))
        ok += 1

    if not dry_run and errors == 0:
        path.write_text("".join(lines_out), encoding="utf-8")
        print(f"Обновлён {path}, загружено/пропущено строк: {ok}", file=sys.stderr)
    elif dry_run:
        print(f"dry-run: было бы обработано записей: {ok}", file=sys.stderr)
    else:
        print(
            "Файл JS не перезаписан из-за ошибок загрузки. Исправьте сеть и запустите снова.",
            file=sys.stderr,
        )
        return 1

    return 0 if errors == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Локальные миниатюры тканей для fabric_std_data.js")
    ap.add_argument("--dry-run", action="store_true", help="только показать объём, без скачивания")
    ap.add_argument(
        "--no-skip",
        action="store_true",
        help="перекачивать файлы даже если уже есть на диске",
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    js_path = root / "static" / "js" / "fabric_std_data.js"
    static_root = root / "static"
    if not js_path.is_file():
        print(f"Нет файла: {js_path}", file=sys.stderr)
        return 1

    return process_js(
        js_path,
        static_root,
        dry_run=args.dry_run,
        skip_existing=not args.no_skip,
    )


if __name__ == "__main__":
    raise SystemExit(main())
