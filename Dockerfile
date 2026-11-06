FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Непривилегированный пользователь. /data хранит базу и загруженные фото (подключается как том)
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app /data \
    && chown app:app /app /data

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=app:app . .

USER app

# Статика админки собирается при сборке образа. Ключ нужен только затем,
# чтобы загрузились настройки, в образ он не попадает.
RUN SECRET_KEY=build-only-key python manage.py collectstatic --noinput

ENV DATABASE_PATH=/data/db.sqlite3 \
    MEDIA_ROOT=/data/media

VOLUME /data
EXPOSE 8000

# По умолчанию запускается веб-часть (админка). Бот: python -m bot.main_bot
CMD ["gunicorn", "FlowerShopBot.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]
