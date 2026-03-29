"""
Flask-приложение калькулятора маркиз.
"""

import hashlib
import json
import os
import smtplib
import threading
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

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

from calculator import calculate, get_pricing, reload_pricing
from pdf_generator import generate_pdf

load_dotenv()

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
        result = calculate(params)
        buf = generate_pdf(result)
        return send_file(
            buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="awning_calculation.pdf",
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
        expected = os.environ.get("ADMIN_PASSWORD", "")
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


if __name__ == "__main__":
    app.run(debug=True)
