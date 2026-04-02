"""
Flask-приложение калькулятора маркиз.
"""

import base64
import hashlib
import json
import os
import shutil
import smtplib
import uuid
import threading
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from typing import Any

import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from calculator import calculate, get_pricing, reload_pricing
from kp_content import get_kp_merged, get_kp_raw, reload_kp_content, save_kp_content
from motor_commercial import default_kp_structure
from pdf_generator import generate_pdf

load_dotenv()

# Vision/OCR: см. https://docs.anthropic.com/en/docs/about-claude/models
ANTHROPIC_OCR_MODEL = os.environ.get("ANTHROPIC_OCR_MODEL", "claude-sonnet-4-6")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# ---------------------------------------------------------------------------
# In-memory кэш расчётов: {md5(params): {result, ts}}
# ---------------------------------------------------------------------------

_CACHE: dict[str, dict] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = 86400        # 24 h
_CACHE_MAX = 1000


def _cache_key(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_get(key: str):
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
            return entry["result"]
        if entry:
            del _CACHE[key]
        return None


def _cache_set(key: str, result: dict) -> None:
    with _CACHE_LOCK:
        if len(_CACHE) >= _CACHE_MAX:
            # Удаляем самую старую запись
            oldest = min(_CACHE, key=lambda k: _CACHE[k]["ts"])
            del _CACHE[oldest]
        _CACHE[key] = {"result": result, "ts": time.time()}


# ---------------------------------------------------------------------------
# PostgreSQL (опционально)
# ---------------------------------------------------------------------------

def _get_db():
    """Возвращает подключение к БД или None, если DATABASE_URL не задан."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return None
    try:
        import psycopg2
        return psycopg2.connect(db_url)
    except Exception:
        return None


def _save_lead(phone: str, city: str, calc_text: str, channel: str = "callback") -> None:
    conn = _get_db()
    if not conn:
        return
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO leads (phone, city, calc_text, channel) VALUES (%s, %s, %s, %s)",
                    (phone, city, calc_text, channel),
                )
    except Exception:
        pass
    finally:
        conn.close()


def _save_calc_history(params_hash: str, result: dict) -> None:
    """Сохраняет результат расчёта для аналитики (таблица calc_history)."""
    conn = _get_db()
    if not conn:
        return
    try:
        payload = json.dumps(result, ensure_ascii=False)
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO calc_history (params_hash, result_json) VALUES (%s, %s::jsonb)",
                    (params_hash, payload),
                )
    except Exception:
        pass
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Уведомления
# ---------------------------------------------------------------------------

def _send_telegram(text: str) -> None:
    token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=8,
        )
    except Exception:
        pass


def _send_email(phone: str, city: str, calc_text: str) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    to_addr = os.environ.get("EMAIL_TO")
    if not all([user, password, to_addr]):
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "📊 Новая заявка — Маркизы"
        msg["From"] = user
        msg["To"] = to_addr
        body = (
            f"<b>Телефон:</b> {phone}<br>"
            f"<b>Город:</b> {city}<br>"
            f"<pre>{calc_text}</pre>"
        )
        msg.attach(MIMEText(body, "html", "utf-8"))
        with smtplib.SMTP(host, port, timeout=8) as srv:
            srv.starttls()
            srv.login(user, password)
            srv.sendmail(user, to_addr, msg.as_string())
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Маршруты
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    pricing = get_pricing()
    ym_id = os.environ.get("YM_ID", "")
    return render_template("index.html", ym_id=ym_id, euro_rate=pricing.get("euro_rate", 100))


# --- API ---

@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    params = request.get_json(force=True)
    if not params:
        return jsonify({"error": "Пустой запрос"}), 400

    key = _cache_key(params)
    cached = _cache_get(key)
    if cached:
        return jsonify(cached)

    try:
        result = calculate(params)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 422

    _cache_set(key, result)
    threading.Thread(target=_save_calc_history, args=(key, result), daemon=True).start()
    return jsonify(result)


@app.route("/api/submit-lead", methods=["POST"])
def api_submit_lead():
    data = request.get_json(force=True) or {}
    phone = data.get("phone", "")
    city = data.get("city", "Не определён")
    calc_text = data.get("calc_text", "")
    channel = data.get("channel", "callback")

    if not phone:
        return jsonify({"error": "Телефон обязателен"}), 400

    tg_text = (
        f"📊 Новая заявка с калькулятора Маркизы\n\n"
        f"📞 Телефон: {phone}\n"
        f"📍 Город: {city}\n\n"
        f"{calc_text}"
    )

    # Уведомления и сохранение — фоновый поток (не блокируем ответ)
    def _notify():
        _send_telegram(tg_text)
        _send_email(phone, city, calc_text)
        _save_lead(phone, city, calc_text, channel)

    threading.Thread(target=_notify, daemon=True).start()
    return jsonify({"ok": True})


@app.route("/api/prices")
def api_prices():
    return jsonify(get_pricing())


@app.route("/reload-prices", methods=["POST"])
def reload_prices():
    """Перечитать awning_pricing.json без рестарта (для обновления прайса)."""
    try:
        pricing = reload_pricing()
        return jsonify({"ok": True, "euro_rate": pricing.get("euro_rate")})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/cache-stats")
def cache_stats():
    with _CACHE_LOCK:
        total = len(_CACHE)
        now = time.time()
        alive = sum(1 for e in _CACHE.values() if (now - e["ts"]) < _CACHE_TTL)
    return jsonify({"total": total, "alive": alive, "max": _CACHE_MAX, "ttl_hours": _CACHE_TTL // 3600})


@app.route("/api/pdf", methods=["POST"])
def api_pdf():
    params = request.get_json(force=True)
    if not params:
        return jsonify({"error": "Пустой запрос"}), 400
    try:
        # Автоматическое переключение ZIP 100 → ZIP 130 при превышении лимитов
        if (params.get("awning_type") == "zip" and params.get("config") == "zip100"):
            w = float(params.get("width", 0))
            h = float(params.get("height", 0))
            if w > 4.0 or h > 3.5:
                params = dict(params)
                params["config"] = "zip130"
        result = calculate(params)
        from datetime import datetime
        kp_date = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        buf = generate_pdf(result, params=params)
        awning_type = params.get("awning_type", "awning")
        filename = f"КП_{awning_type}_{kp_date}.pdf"
        return send_file(
            buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 422


# ---------------------------------------------------------------------------
# Админ-панель
# ---------------------------------------------------------------------------

def _admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        # Пароль: переменная ADMIN_PASSWORD в .env / на сервере; иначе значение по умолчанию ниже
        expected = (os.environ.get("ADMIN_PASSWORD") or "andrew009").strip()
        if password and password == expected:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Неверный пароль"
    return render_template("admin/login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@_admin_required
def admin_dashboard():
    conn = _get_db()
    leads = []
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, phone, city, channel, calc_text, created_at "
                    "FROM leads ORDER BY created_at DESC LIMIT 100"
                )
                cols = [d[0] for d in cur.description]
                leads = [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception:
            pass
        finally:
            conn.close()

    with _CACHE_LOCK:
        now = time.time()
        cache_info = {
            "total": len(_CACHE),
            "alive": sum(1 for e in _CACHE.values() if (now - e["ts"]) < _CACHE_TTL),
            "max": _CACHE_MAX,
        }

    pricing = get_pricing()
    return render_template(
        "admin/dashboard.html",
        leads=leads,
        cache_info=cache_info,
        pricing=pricing,
    )


@app.route("/admin/settings")
@_admin_required
def admin_settings():
    """Прайсы, матрицы, тексты и изображения КП."""
    return render_template("admin/settings.html")


_MATRIX_TABLE_KEYS = (
    "PRICES_OPEN",
    "PRICES_SEMI",
    "PRICES_CASSETTE",
    "PRICES_G400",
    "PRICES_G450",
    "ZIP100",
    "ZIP130",
)


@app.route("/admin/api/pricing-full", methods=["GET", "POST"])
@_admin_required
def admin_api_pricing_full():
    """Чтение / полная замена awning_pricing.json (с резервной копией)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "static", "data", "awning_pricing.json")
    if request.method == "GET":
        with open(path, encoding="utf-8") as f:
            return jsonify(json.load(f))
    body = request.get_json(force=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400
    try:
        int(body.get("euro_rate", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Некорректный euro_rate"}), 400
    for k in _MATRIX_TABLE_KEYS:
        if k in body and not isinstance(body[k], dict):
            return jsonify({"error": f"Таблица {k} должна быть объектом"}), 400
    try:
        bak = path + ".bak"
        if os.path.isfile(path):
            shutil.copy2(path, bak)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        return jsonify({"error": str(exc)}), 500
    with _CACHE_LOCK:
        _CACHE.clear()
    reload_pricing()
    return jsonify({"ok": True})


@app.route("/admin/api/kp-content", methods=["GET", "POST"])
@_admin_required
def admin_api_kp_content():
    if request.method == "GET":
        return jsonify({
            "merged": get_kp_merged(),
            "stored": get_kp_raw(),
        })
    body = request.get_json(force=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400
    try:
        save_kp_content(body)
    except OSError as exc:
        return jsonify({"error": str(exc)}), 500
    return jsonify({"ok": True})


@app.route("/admin/api/kp-defaults", methods=["GET"])
@_admin_required
def admin_api_kp_defaults():
    return jsonify(default_kp_structure())


@app.route("/admin/api/kp-upload", methods=["POST"])
@_admin_required
def admin_api_kp_upload():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "Файл не передан"}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        return jsonify({"error": "Допустимы JPG, PNG, WEBP, GIF"}), 400
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(base_dir, "static", "img", "kp_admin")
    os.makedirs(folder, exist_ok=True)
    safe = secure_filename(f.filename) or "image"
    name = f"{uuid.uuid4().hex[:12]}_{safe}"
    dest = os.path.join(folder, name)
    try:
        f.save(dest)
    except OSError as exc:
        return jsonify({"error": str(exc)}), 500
    url = "/static/img/kp_admin/" + name
    return jsonify({"ok": True, "url": url})


@app.route("/admin/update-euro-rate", methods=["POST"])
@_admin_required
def admin_update_euro_rate():
    """Обновляет курс EUR/RUB в JSON-файле прайса."""
    try:
        rate = int(request.form.get("euro_rate", 100))
        if rate <= 0:
            raise ValueError("Курс должен быть положительным")
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "static", "data", "awning_pricing.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["euro_rate"] = rate
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        reload_pricing()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------------------
# OCR прайсов через Claude Vision
# ---------------------------------------------------------------------------

# Справочник таблиц: имя → описание для промпта
_PRICE_TABLES = {
    "PRICES_OPEN": {
        "name": "Открытая локтевая маркиза",
        "row_label": "ширина (ширина)",
        "col_label": "вылет (вынос)",
        "expected_rows": "3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0",
        "expected_cols": "1.5, 2.0, 2.5, 3.0, 3.5",
    },
    "PRICES_SEMI": {
        "name": "Полукассетная локтевая маркиза",
        "row_label": "ширина",
        "col_label": "вылет",
        "expected_rows": "3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0",
        "expected_cols": "1.5, 2.0, 2.5, 3.0, 3.5",
    },
    "PRICES_CASSETTE": {
        "name": "Кассетная локтевая маркиза",
        "row_label": "ширина",
        "col_label": "вылет",
        "expected_rows": "3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0",
        "expected_cols": "1.5, 2.0, 2.5, 3.0, 3.5",
    },
    "PRICES_G400": {
        "name": "Витринная G400 Italy — открытая (Gaviota)",
        "row_label": "ширина",
        "col_label": "вылет",
        "expected_rows": "3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0",
        "expected_cols": "0.8, 1.0, 1.4",
    },
    "PRICES_G450": {
        "name": "Витринная G450 Desert — кассетная (Gaviota)",
        "row_label": "ширина",
        "col_label": "вылет",
        "expected_rows": "3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0",
        "expected_cols": "0.8, 1.0, 1.4",
    },
    "ZIP100": {
        "name": "Вертикальная ZIP маркиза 100",
        "row_label": "ширина",
        "col_label": "высота",
        "expected_rows": "1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0",
        "expected_cols": "1.0, 1.5, 2.0, 2.5, 3.0, 3.5",
    },
    "ZIP130": {
        "name": "Вертикальная ZIP маркиза 130",
        "row_label": "ширина",
        "col_label": "высота",
        "expected_rows": "1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0",
        "expected_cols": "1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0",
    },
}


def _fmt_dim(v: str) -> str:
    """Нормализует ключ размера: "3" → "3.0", "3.50" → "3.5"."""
    return f"{float(str(v).strip()):.1f}"


def _parse_price_int(v) -> int:
    """Парсит цену: "4 512" → 4512, "4512.0" → 4512."""
    s = str(v).replace(" ", "").replace("\u00a0", "").replace(",", ".")
    return int(float(s))


def _normalize_ocr(parsed: dict) -> dict:
    """Нормализует результат OCR: ключи → "X.Y", цены → int, сортировка."""
    widths_raw = parsed.get("widths", [])
    projs_raw = parsed.get("projections", parsed.get("heights", []))
    prices_raw = parsed.get("prices", {})

    widths = sorted(set(_fmt_dim(w) for w in widths_raw), key=float)
    projs = sorted(set(_fmt_dim(p) for p in projs_raw), key=float)

    prices: dict[str, dict[str, int]] = {}
    for w_raw, row in prices_raw.items():
        w = _fmt_dim(w_raw)
        prices[w] = {}
        for p_raw, price in row.items():
            p = _fmt_dim(p_raw)
            try:
                prices[w][p] = _parse_price_int(price)
            except (ValueError, TypeError):
                prices[w][p] = 0

    return {"widths": widths, "projections": projs, "prices": prices}


def _build_ocr_prompt(tinfo: dict) -> str:
    extra_block = ""
    er = tinfo.get("extra_rules")
    if er:
        extra_block = f"\n\nADDITIONAL RULES:\n{er}\n"

    return f"""You are a precise OCR engine for awning price tables.

TASK: Extract ALL prices from this price table image with MAXIMUM accuracy.

TABLE TYPE: {tinfo['name']}
TABLE STRUCTURE (how to read the image):
- LEFT column / row headers: {tinfo['row_label']}
- TOP row / column headers: {tinfo['col_label']}
- Each cell contains ONE integer price (no asterisks, no secondary prices)

EXPECTED values along the LEFT axis: {tinfo['expected_rows']}
EXPECTED values along the TOP axis: {tinfo['expected_cols']}
{extra_block}
JSON OUTPUT (mandatory mapping — do not swap):
- "widths" = list of all WIDTH keys in meters (outer keys of "prices")
- "projections" = list of all PROJECTION keys in meters (inner keys of "prices")
- "prices"[width][projection] = integer EUR

RULES:
1. If a cell has two numbers, take ONLY the first (larger) one — ignore asterisk prices
2. Prices may have spaces as thousands separators: "4 512" = 4512
3. Format all dimension keys as "X.Y" (one decimal, e.g. "3.0", "1.5")
4. Return ONLY valid JSON — no markdown, no explanation

REQUIRED JSON format:
{{
  "widths": ["3.0", "3.5", "4.0", ...],
  "projections": ["1.5", "2.0", "2.5", ...],
  "prices": {{
    "3.0": {{"1.5": 545, "2.0": 595, "2.5": 650, "3.0": 715, "3.5": 790}},
    "3.5": {{"1.5": 585, ...}},
    ...
  }}
}}"""


def _build_verify_prompt(normalized: dict, tinfo: dict) -> tuple[str, list[tuple]]:
    """Строит промпт верификации для угловых ячеек и первой/последней строки."""
    widths = normalized["widths"]
    projs = normalized["projections"]
    prices = normalized["prices"]

    cells_to_check: list[tuple] = []
    seen: set[tuple] = set()

    def _add(w: str, p: str) -> None:
        if (w, p) not in seen and w in prices and p in prices.get(w, {}):
            seen.add((w, p))
            cells_to_check.append((w, p, prices[w][p]))

    # Первая и последняя строка полностью
    for w in [widths[0], widths[-1]]:
        for p in projs:
            _add(w, p)
    # Первый и последний столбец всех строк
    for w in widths:
        for p in [projs[0], projs[-1]]:
            _add(w, p)

    if not cells_to_check:
        return "", []

    lines = [f"  {tinfo['row_label']}={w}м, {tinfo['col_label']}={p}м → extracted: {price}"
             for w, p, price in cells_to_check]
    cells_text = "\n".join(lines)

    prompt = f"""You are verifying OCR-extracted awning prices.

TABLE: {tinfo['name']}
Check ONLY these specific cells from the image:

{cells_text}

Return ONLY a JSON object with corrections where my value is WRONG:
{{
  "corrections": [
    {{"width": "3.0", "projection": "1.5", "correct_price": 545}},
    ...
  ]
}}

If all values are correct return: {{"corrections": []}}
Use "projection" key for both projection and height values.
Return ONLY JSON — no markdown."""

    return prompt, cells_to_check


def _run_claude_price_ocr(
    api_key: str,
    b64: str,
    media_type: str,
    tinfo: dict,
) -> tuple[dict, int]:
    """OCR матрицы цен через Claude Vision. Возвращает (normalized, corrections_applied)."""
    import anthropic as _anthropic

    client = _anthropic.Anthropic(api_key=api_key)
    ocr_prompt = _build_ocr_prompt(tinfo)
    resp1 = client.messages.create(
        model=ANTHROPIC_OCR_MODEL,
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": ocr_prompt},
            ],
        }],
    )
    raw1 = resp1.content[0].text.strip()
    if raw1.startswith("```"):
        raw1 = raw1.split("\n", 1)[1] if "\n" in raw1 else raw1
        raw1 = raw1.rsplit("```", 1)[0].strip()

    parsed = json.loads(raw1)
    normalized = _normalize_ocr(parsed)

    corrections_applied = 0
    verify_prompt, _cells = _build_verify_prompt(normalized, tinfo)

    if verify_prompt:
        resp2 = client.messages.create(
            model=ANTHROPIC_OCR_MODEL,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                    {"type": "text", "text": verify_prompt},
                ],
            }],
        )
        raw2 = resp2.content[0].text.strip()
        if raw2.startswith("```"):
            raw2 = raw2.split("\n", 1)[1] if "\n" in raw2 else raw2
            raw2 = raw2.rsplit("```", 1)[0].strip()

        try:
            verify_data = json.loads(raw2)
            for corr in verify_data.get("corrections", []):
                w_key = _fmt_dim(corr.get("width", ""))
                p_key = _fmt_dim(corr.get("projection", ""))
                correct_price = _parse_price_int(corr.get("correct_price", 0))
                if (w_key in normalized["prices"]
                        and p_key in normalized["prices"][w_key]
                        and normalized["prices"][w_key][p_key] != correct_price):
                    normalized["prices"][w_key][p_key] = correct_price
                    corrections_applied += 1
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    return normalized, corrections_applied


# --- Decolife: отдельные JSON по линейкам (G90, G100, G500 …) ---

_DECOLIFE_LINE_FILES: dict[str, str] = {
    "open_elbow": "decolife_open_elbow.json",
    "semi_elbow": "decolife_semi_elbow.json",
    "cassette_elbow": "decolife_cassette_elbow.json",
}

_DECOLIFE_LINE_LABELS: dict[str, str] = {
    "open_elbow": "Локтевая открытая",
    "semi_elbow": "Локтевая полукассетная",
    "cassette_elbow": "Локтевая кассетная",
}

_DECOLIFE_TIER_LABELS: dict[str, str] = {
    "gaviota": "Ткань 1 · Gaviota (Acryl)",
    "sattler_cat2": "Ткань 2 · Sattler Elements, Sattler Solid",
    "sattler_cat3": "Ткань 3 · Sattler Lumera, Sattler Lumera 3D",
}


def _decolife_file_path(line: str) -> str:
    fn = _DECOLIFE_LINE_FILES.get(line)
    if not fn:
        raise ValueError("bad line")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "static", "data", fn)


def _load_decolife_doc(line: str) -> dict[str, Any]:
    path = _decolife_file_path(line)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _decolife_tinfo_for_ocr(series: str, tier: str, table: dict[str, Any]) -> dict[str, str]:
    tier_ru = _DECOLIFE_TIER_LABELS.get(tier, tier)
    widths = sorted((table or {}).keys(), key=lambda x: float(x))
    projs: set[str] = set()
    for row in (table or {}).values():
        if isinstance(row, dict):
            projs.update(row.keys())
    proj_list = sorted(projs, key=lambda x: float(x))
    extra = (
        "ВАЖНО для прайсов Decolife/Gaviota: на одном листе часто идут ПОДРЯД три таблицы "
        "(ткань 1 Gaviota, ткань 2 Elements/Solids, ткань 3 Lumera). Извлеки ТОЛЬКО ту матрицу, "
        "которая соответствует заголовку и блоку с названием серии выше. Игнорируй остальные блоки. "
        "Пустые ячейки «лесенки» (нет комбинации ширина×вынос) не заполняй выдуманными числами."
    )
    map_note = (
        "На листах Decolife ширина чаще в ВЕРХНЕЙ строке заголовков, вынос — в ЛЕВОЙ колонке. "
        "В JSON всё равно: внешние ключи prices = ширина (м), внутренние = вынос (м)."
    )
    return {
        "name": f"{series} — {tier_ru}",
        "row_label": "вынос (проекция), м — обычно левая колонка",
        "col_label": "ширина, м — обычно верхняя строка заголовков",
        "expected_rows": ", ".join(proj_list) if proj_list else "определи по изображению",
        "expected_cols": ", ".join(widths) if widths else "определи по изображению",
        "extra_rules": extra + " " + map_note,
    }


def _clean_decolife_prices_table(prices_in: dict) -> dict[str, dict[str, int]]:
    """Нормализует матрицу для записи в decolife_*.json."""
    out: dict[str, dict[str, int]] = {}
    for w_raw, row in (prices_in or {}).items():
        if not isinstance(row, dict):
            continue
        try:
            w = _fmt_dim(str(w_raw))
        except (ValueError, TypeError):
            continue
        inner: dict[str, int] = {}
        for p_raw, val in row.items():
            if val is None or val == "":
                continue
            try:
                p = _fmt_dim(str(p_raw))
                inner[p] = int(float(str(val).replace(",", ".").replace(" ", "").replace("\u00a0", "")))
            except (ValueError, TypeError):
                continue
        if inner:
            out[w] = inner
    return out


@app.route("/admin/parse-price-image", methods=["POST"])
@_admin_required
def admin_parse_price_image():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY не задан в .env"}), 400

    table_name = request.form.get("table_name", "")
    if table_name not in _PRICE_TABLES:
        return jsonify({"error": f"Неизвестная таблица: {table_name}"}), 400

    img_file = request.files.get("image")
    if not img_file:
        return jsonify({"error": "Файл изображения не передан"}), 400

    img_bytes = img_file.read()
    b64 = base64.b64encode(img_bytes).decode()
    ext = img_file.filename.rsplit(".", 1)[-1].lower() if "." in img_file.filename else "jpeg"
    media_type = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"

    tinfo = dict(_PRICE_TABLES[table_name])

    try:
        normalized, corrections_applied = _run_claude_price_ocr(api_key, b64, media_type, tinfo)
        total_cells = sum(len(row) for row in normalized["prices"].values())
        return jsonify({
            "ok": True,
            "table_name": table_name,
            "table_label": tinfo["name"],
            "data": normalized,
            "stats": {
                "cells": total_cells,
                "corrections": corrections_applied,
                "widths": len(normalized["widths"]),
                "projections": len(normalized["projections"]),
            },
        })
    except json.JSONDecodeError as exc:
        return jsonify({"error": f"Claude вернул невалидный JSON: {exc}"}), 422
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/admin/api/decolife-catalog", methods=["GET"])
@_admin_required
def admin_api_decolife_catalog():
    lines_out: list[dict] = []
    for line_key in _DECOLIFE_LINE_FILES:
        try:
            doc = _load_decolife_doc(line_key)
        except OSError:
            doc = {}
        models = doc.get("models") or {}
        mlist: list[dict] = []
        for mid, meta in models.items():
            if not isinstance(meta, dict):
                continue
            tables = meta.get("tables") or {}
            mlist.append({
                "id": mid,
                "series": meta.get("series", mid),
                "short_label": meta.get("short_label", mid),
                "tiers": sorted(tables.keys()),
                "order": meta.get("order", 99),
            })
        mlist.sort(key=lambda x: (x["order"], x["id"]))
        lines_out.append({
            "key": line_key,
            "label": _DECOLIFE_LINE_LABELS.get(line_key, line_key),
            "models": mlist,
        })
    return jsonify({"lines": lines_out, "tier_labels": _DECOLIFE_TIER_LABELS})


@app.route("/admin/api/decolife-matrix", methods=["GET"])
@_admin_required
def admin_api_decolife_matrix_get():
    line = request.args.get("line", "")
    model_id = request.args.get("model_id", "")
    tier = request.args.get("tier", "")
    if line not in _DECOLIFE_LINE_FILES:
        return jsonify({"error": "Неизвестная линейка"}), 400
    if not model_id or not tier:
        return jsonify({"error": "Укажите model_id и tier"}), 400
    doc = _load_decolife_doc(line)
    models = doc.get("models") or {}
    meta = models.get(model_id)
    if not isinstance(meta, dict):
        return jsonify({"error": "Модель не найдена"}), 404
    tables = meta.get("tables") or {}
    table = tables.get(tier)
    if table is None:
        table = {}
    elif not isinstance(table, dict):
        table = {}
    widths = sorted(table.keys(), key=lambda x: float(x))
    projs: set[str] = set()
    for row in table.values():
        if isinstance(row, dict):
            projs.update(row.keys())
    proj_list = sorted(projs, key=lambda x: float(x))
    return jsonify({
        "line": line,
        "model_id": model_id,
        "tier": tier,
        "series": meta.get("series", model_id),
        "short_label": meta.get("short_label", model_id),
        "tier_label": _DECOLIFE_TIER_LABELS.get(tier, tier),
        "prices": table,
        "widths": widths,
        "projections": proj_list,
    })


@app.route("/admin/api/decolife-matrix", methods=["POST"])
@_admin_required
def admin_api_decolife_matrix_save():
    body = request.get_json(force=True) or {}
    line = body.get("line", "")
    model_id = body.get("model_id", "")
    tier = body.get("tier", "")
    prices_in = body.get("prices", {})
    if line not in _DECOLIFE_LINE_FILES:
        return jsonify({"error": "Неизвестная линейка"}), 400
    if not model_id or not tier:
        return jsonify({"error": "Укажите model_id и tier"}), 400
    path = _decolife_file_path(line)
    try:
        doc = _load_decolife_doc(line)
    except OSError as exc:
        return jsonify({"error": str(exc)}), 500
    models = doc.setdefault("models", {})
    meta = models.get(model_id)
    if not isinstance(meta, dict):
        return jsonify({"error": "Модель не найдена"}), 404
    tables = meta.setdefault("tables", {})
    cleaned = _clean_decolife_prices_table(prices_in)
    tables[tier] = cleaned
    bak = path + ".bak"
    try:
        shutil.copy2(path, bak)
    except OSError:
        pass
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        return jsonify({"error": f"Ошибка записи: {exc}"}), 500
    with _CACHE_LOCK:
        _CACHE.clear()
    reload_pricing()
    total = sum(len(r) for r in cleaned.values())
    return jsonify({"ok": True, "cells_written": total})


@app.route("/admin/parse-decolife-price-image", methods=["POST"])
@_admin_required
def admin_parse_decolife_price_image():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY не задан в .env"}), 400
    line = request.form.get("line", "")
    model_id = request.form.get("model_id", "")
    tier = request.form.get("tier", "")
    if line not in _DECOLIFE_LINE_FILES:
        return jsonify({"error": "Неизвестная линейка"}), 400
    if not model_id or not tier:
        return jsonify({"error": "Укажите model_id и tier"}), 400
    try:
        doc = _load_decolife_doc(line)
    except OSError as exc:
        return jsonify({"error": str(exc)}), 500
    meta = (doc.get("models") or {}).get(model_id)
    if not isinstance(meta, dict):
        return jsonify({"error": "Модель не найдена"}), 404
    series = str(meta.get("series", model_id))
    table = (meta.get("tables") or {}).get(tier, {})
    if not isinstance(table, dict):
        table = {}
    tinfo = _decolife_tinfo_for_ocr(series, tier, table)

    img_file = request.files.get("image")
    if not img_file:
        return jsonify({"error": "Файл изображения не передан"}), 400
    img_bytes = img_file.read()
    b64 = base64.b64encode(img_bytes).decode()
    ext = img_file.filename.rsplit(".", 1)[-1].lower() if "." in img_file.filename else "jpeg"
    media_type = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"

    try:
        normalized, corrections_applied = _run_claude_price_ocr(api_key, b64, media_type, tinfo)
        total_cells = sum(len(row) for row in normalized["prices"].values())
        return jsonify({
            "ok": True,
            "line": line,
            "model_id": model_id,
            "tier": tier,
            "table_label": tinfo["name"],
            "data": normalized,
            "stats": {
                "cells": total_cells,
                "corrections": corrections_applied,
                "widths": len(normalized["widths"]),
                "projections": len(normalized["projections"]),
            },
        })
    except json.JSONDecodeError as exc:
        return jsonify({"error": f"Claude вернул невалидный JSON: {exc}"}), 422
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


_AUTOMATION_SEGMENTS = frozenset({"elbow", "storefront", "zip"})


def _fix_gaviota_keys_in_automation(obj: Any) -> Any:
    """Claude может вернуть gaviota — в JSON прайса используется ключ decolife."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            nk = str(k)
            if nk.lower() == "gaviota":
                nk = "decolife"
            out[nk] = _fix_gaviota_keys_in_automation(v)
        return out
    if isinstance(obj, list):
        return [_fix_gaviota_keys_in_automation(x) for x in obj]
    return obj


def _automation_ocr_prompt(segment: str) -> str:
    zip_block = ""
    if segment == "zip":
        zip_block = (
            'Include "motor_zip": {"somfy_small": int, "somfy_large": int, "simu": int, "decolife": int} '
            "from the motor section (Somfy often has two torque variants → small vs large).\n"
        )
    else:
        zip_block = (
            'Include "motor_body": {"somfy": int, "simu": int, "decolife": int} — one baseline tubular motor EUR per brand '
            "(if two rows per brand, take the first/lower torque line).\n"
        )
    return f"""Extract automation prices from this Russian awning price sheet (sections like «Модели двигателей», «Пульты», «Солнечно-ветровая автоматика», «Ручное управление»).

LAYOUT: three brand columns Somfy | Simu | third column may be labeled Decolife or Gaviota — in JSON always use the key "decolife" for that column (never "gaviota").

Return ONLY valid JSON, no markdown.

{zip_block}
Always include:
- "manual_eur": int (редуктор / ручное, often 50)
- "remotes": {{
    "somfy": {{"single": {{"label": "string", "eur": int}}, "dual_light": {{...}}, "multi": {{...}}}},
    "simu": {{...}},
    "decolife": {{...}}
  }}
  Map rows: 1st remote row → single (1 channel), 2nd → dual_light (2 channels / patio), 3rd → multi (many channels / LCD). If Somfy shows "40/70" style, use 40 for single-like and 70 for dual-like.
- "sensor_radio": {{"somfy": int, "simu": int, "decolife": int}} — first wind/radio sensor column price per brand
- "sensor_speed": {{"somfy": int, "simu": int, "decolife": int}} — sun+wind / 3D / EOSUN style row per brand

Integers only. Labels in Russian or Latin as on the sheet."""


def _run_claude_automation_ocr(api_key: str, b64: str, media_type: str, segment: str) -> dict[str, Any]:
    import anthropic as _anthropic

    client = _anthropic.Anthropic(api_key=api_key)
    prompt = _automation_ocr_prompt(segment)
    resp = client.messages.create(
        model=ANTHROPIC_OCR_MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        raw = raw.rsplit("```", 1)[0].strip()
    parsed = json.loads(raw)
    return _fix_gaviota_keys_in_automation(parsed)


@app.route("/admin/parse-automation-price-image", methods=["POST"])
@_admin_required
def admin_parse_automation_price_image():
    """OCR прайса «Другие варианты управления» → JSON сегмента _automation_eur."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY не задан в .env"}), 400
    segment = (request.form.get("segment") or "").strip()
    if segment not in _AUTOMATION_SEGMENTS:
        return jsonify({"error": "Укажите segment: elbow, storefront или zip"}), 400
    img_file = request.files.get("image")
    if not img_file:
        return jsonify({"error": "Файл изображения не передан"}), 400
    img_bytes = img_file.read()
    b64 = base64.b64encode(img_bytes).decode()
    ext = img_file.filename.rsplit(".", 1)[-1].lower() if "." in img_file.filename else "jpeg"
    media_type = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
    try:
        data = _run_claude_automation_ocr(api_key, b64, media_type, segment)
        return jsonify({"ok": True, "segment": segment, "data": data})
    except json.JSONDecodeError as exc:
        return jsonify({"error": f"Claude вернул невалидный JSON: {exc}"}), 422
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/admin/apply-parsed-prices", methods=["POST"])
@_admin_required
def admin_apply_parsed_prices():
    """Заменяет таблицу в awning_pricing.json и сбрасывает кэш."""
    body = request.get_json(force=True) or {}
    table_name = body.get("table_name", "")
    prices_in = body.get("prices", {})  # {width: {projection: price}}

    if table_name not in _PRICE_TABLES:
        return jsonify({"error": f"Неизвестная таблица: {table_name}"}), 400
    if not prices_in:
        return jsonify({"error": "Пустые данные цен"}), 400

    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "static", "data", "awning_pricing.json")

    try:
        with open(path, encoding="utf-8") as f:
            pricing = json.load(f)

        # Нормализуем и записываем
        new_table: dict[str, dict[str, int]] = {}
        for w_raw, row in prices_in.items():
            w = _fmt_dim(w_raw)
            new_table[w] = {}
            for p_raw, price in row.items():
                p = _fmt_dim(p_raw)
                try:
                    new_table[w][p] = int(float(price))
                except (ValueError, TypeError):
                    new_table[w][p] = 0

        pricing[table_name] = new_table

        with open(path, "w", encoding="utf-8") as f:
            json.dump(pricing, f, ensure_ascii=False, indent=2)

    except Exception as exc:
        return jsonify({"error": f"Ошибка записи файла: {exc}"}), 500

    # Сброс кэша расчётов + перезагрузка прайса
    with _CACHE_LOCK:
        _CACHE.clear()
    reload_pricing()

    total_cells = sum(len(row) for row in new_table.values())
    return jsonify({"ok": True, "table_name": table_name, "cells_written": total_cells})


if __name__ == "__main__":
    app.run(debug=True)
