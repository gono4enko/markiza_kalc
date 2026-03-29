"""
Flask-приложение калькулятора маркиз.
Реализация эндпоинтов — Фаза 2.
"""
from flask import Flask

app = Flask(__name__)


if __name__ == '__main__':
    app.run(debug=True)
