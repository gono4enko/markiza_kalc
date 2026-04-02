# Калькулятор маркиз (Flask)

Серверный расчёт стоимости, PDF КП, заявки (Telegram + SMTP), админка с OCR прайсов.

**Репозиторий:** [github.com/gono4enko/markiza_kalc](https://github.com/gono4enko/markiza_kalc) — клонирование и деплой с GitHub.

## Быстрый старт (локально)

На macOS (Homebrew Python) без venv `pip install` в систему обычно **запрещён** (PEP 668) — приложение не найдёт `requests`, `Flask` и т.д. Сначала создайте окружение.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # заполните при необходимости
export FLASK_APP=app.py
flask run --host 127.0.0.1 --port 5000
# или: python app.py
```

Откройте http://127.0.0.1:5000/

## Деплой на сервер

См. [docs/DEPLOY.md](docs/DEPLOY.md) — systemd, Nginx, PostgreSQL, GitHub Actions.

## Проверка API (curl)

```bash
# Расчёт (одна позиция, локтевая)
curl -s -X POST http://127.0.0.1:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"awning_type":"standard","config":"open","width":4,"projection":3,"fabric":"gaviota","frame_color":"white","control":"electric","motor_brand":"decolife","sensor_type":"none","lighting_option":"none","installation":"none"}' | head -c 400

# Перечитать прайс
curl -s -X POST http://127.0.0.1:5000/reload-prices
```

PDF и лиды требуют полного тела запроса как в UI; без `.env` Telegram/SMTP просто не отправятся.
