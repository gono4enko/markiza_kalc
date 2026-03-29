# Деплой калькулятора маркиз (reg.ru, ISPmanager)

## Требования

- Python 3.11+ (рекомендуется 3.12/3.13)
- PostgreSQL (опционально: лиды и история расчётов)
- Nginx
- Виртуальное окружение в каталоге приложения

## 1. Клонирование и зависимости

```bash
cd /var/www
git clone https://github.com/YOUR_ORG/awning-calculator.git
cd awning-calculator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Переменные окружения

```bash
cp .env.example .env
nano .env   # SECRET_KEY, DATABASE_URL, TG_*, SMTP_*, ADMIN_PASSWORD, YM_ID, ANTHROPIC_API_KEY
chmod 600 .env
```

## 3. База данных

```bash
psql "$DATABASE_URL" -f migrations/init.sql
```

Без `DATABASE_URL` приложение работает, но заявки и `calc_history` не пишутся в БД.

## 4. Логи Gunicorn

Пути заданы в [gunicorn.conf.py](../gunicorn.conf.py):

```bash
sudo mkdir -p /var/log/awning-calculator
sudo chown www-data:www-data /var/log/awning-calculator
```

При другом пользователе в unit-файле — смените владельца каталога логов.

## 5. systemd

Скопируйте [deploy/awning-calculator.service](../deploy/awning-calculator.service) в `/etc/systemd/system/`, отредактируйте:

- `User` / `Group` — пользователь сайта (часто не `www-data` на shared-хостинге)
- `WorkingDirectory` / `EnvironmentFile` / `ExecStart` — если путь не `/var/www/awning-calculator`

```bash
sudo cp deploy/awning-calculator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now awning-calculator
sudo systemctl status awning-calculator
```

## 6. Nginx

Используйте [deploy/nginx-snippet.conf](../deploy/nginx-snippet.conf) как основу: `server_name`, SSL, `alias` для `/static/` должен указывать на реальный `WorkingDirectory/static/`.

Проверка:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 7. GitHub Actions

Workflow [.github/workflows/deploy.yml](../.github/workflows/deploy.yml): при push в `main` выполняется SSH-команда на сервере. Секреты репозитория:

| Секрет | Описание |
|--------|----------|
| `SSH_HOST` | хост (например vip252.hosting.reg.ru) |
| `SSH_USER` | SSH-пользователь |
| `SSH_PRIVATE_KEY` | приватный ключ |
| `SSH_PORT` | порт SSH; если не задан в GitHub, в workflow подставляется **22** |

На сервере путь в скрипте должен совпадать с `WorkingDirectory` (по умолчанию `/var/www/awning-calculator`).

## 8. Быстрая проверка после выкладки

- Открыть `/` — калькулятор
- Расчёт → ответ JSON с `total` / `rows`
- Кнопка PDF → скачивание файла
- Заявка с телефоном → запись в `leads` (если БД есть)
- `/admin/login` — дашборд
- В админке «Перечитать JSON» — `POST /reload-prices`
