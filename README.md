# project_flower_shop

## 1. Общая информация

**FlowerShopBot** — Telegram-бот для онлайн-продажи букетов в Красноярске.  
Бот обеспечивает удобный подбор и оформление заказа по шагам, валидацию данных и передачу заказов курьеру.

### Функциональность:
- Выбор букета по событию и бюджету
- Пошаговое оформление заказа с валидацией данных
- Добавление открытки
- Запись консультаций для связи с флористом
- Передача заказа курьеру через Telegram
- Хранение данных о заказах и консультациях в базе данных через Django ORM

---

## 2. Структура проекта

```
├── FlowerShopBot/            # Django-проект
│   ├── settings.py           # Настройки (база, пути, installed_apps)
│   └── urls.py               # URL-роутинг (в основном для админки)
│
├── bot/                      # Логика Telegram-бота
│   ├── handlers/             # Хендлеры сообщений
│   ├── logic/                # Бизнес-логика (валидация, обработка заказов)
│   ├── main_bot.py           # Запуск бота
│   ├── message_tools.py      # Безопасная работа с сообщениями
│   ├── logging_tools.py      # Централизованное логирование
│   ├── exceptions.py         # Кастомные исключения (валидация и ошибки)
│   └── keyboards.py          # Генерация inline-кнопок
│
├── media/                    # Фото букетов, загружаемые через админку
│   └── bouquets/
│
├── manage.py                 # Django CLI
├── requirements.txt          # Зависимости проекта
├── README.md                 # Документация
└── .env                      # Секреты: токены, ID
```

---

## 3. Основные модули

### 3.1 main_bot.py
- Инициализация Django и токена Telegram
- Настройка и регистрация всех хендлеров
- Запуск `updater.start_polling()`

### 3.2 Хендлеры `bot/handlers/`
- `start_handlers.py` — `/start`, выбор начального сценария: букеты, событие, консультация
- `catalog_handlers.py` — фильтрация по бюджету/событию, листание букетов
- `order_handlers.py` — пошаговая обработка заказа (имя → адрес → дата → телефон)
- `consult_handlers.py` — консультация, ввод телефона
- `keyboards.py` — генерация inline-кнопок меню

### 3.3 Логика `bot/logic/`
- `order_flow.py`:
  - `create_order`, `set_contact_info`, `confirm_order`
  - Используются кастомные исключения: `InvalidPhoneError`, `InvalidDateTimeError`, `OrderSaveError`
- `consultation_flow.py`:
  - `request_consultation` — проверка номера, сохранение заявки
- `validators.py`:
  - `normalize_phone`, `validate_phone`, `normalize_datetime`
  - Поддержка форматов: `сегодня 14:00`, `2025-03-27T14:00`, `dd.mm.yyyy hh:mm`
- `data_access.py`:
  - Слой доступа к данным Django: `get_bouquets`, `get_compositions`, `save_order`, `save_consultation`

---

## 4. Валидация и логирование

- Все ошибки валидации логируются через `logging_tools.py`, в файл `logs/bot.log`
- Применяется `RotatingFileHandler`
- Кастомные исключения:
  - `InvalidPhoneError`
  - `InvalidDateTimeError`
  - `OrderSaveError`
  - `ConsultationSaveError`
  - `MissingRequiredFieldError`
  - `UnknownOrderStepError`
  - `MissingOrderDataError`
  - `EmptyBouquetListError`
- Обработка исключений централизована в хендлерах

---

## 5. Настройка и запуск

```bash
# 1. Клонируем репозиторий
git clone ...

# 2. Виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate.bat # Windows

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Создаём .env и прописываем токен
cp .env.example .env
# TELEGRAM_TOKEN=...
# COURIER_ID=...
# FLORIST_ID=...

# 5. Применяем миграции
python manage.py migrate

# 6. Запускаем Django-сервер (админка)
python manage.py runserver

# 7. Запускаем бота
python -m bot.main_bot
```

---

## 6. Админка Django

Для удобного управления ассортиментом:

### Что можно управлять через админку:
- Букеты (`Bouquet`) — имя, цена, фото, описание, поэтический текст
- Композиции (`Composition`) — событие, связанные букеты
- Заказы (`Order`, `OrderItem`) — информация о клиенте и статус
- Консультации (`Consultation`) — заявки на обратный звонок

### Как попасть:
- Создать суперпользователя:
  ```bash
  python manage.py createsuperuser
  ```
- Перейти в браузере:
  ```
  http://127.0.0.1:8000/admin/
  ```

---

## 7. Подключение базы данных

### По умолчанию:
Используется SQLite (в `settings.py`):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Для продакшена:
Рекомендуется подключить PostgreSQL или другую СУБД:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'flowerdb',
        'USER': 'botuser',
        'PASSWORD': 'securepassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Не забудь установить:
```bash
pip install psycopg2-binary
```

---

## 8. Деплой (базовые шаги)

1. Поднять VPS или хостинг с поддержкой Python (например, Render, DigitalOcean, Railway)
2. Установить Python, PostgreSQL
3. Перенести файлы проекта
4. Настроить `.env`, окружение и зависимости
5. Настроить `supervisor` или `systemd` для запуска бота
6. Настроить `nginx` + `gunicorn`, если будет использоваться веб-интерфейс или webhook
7. Подключить домен/SSL, если требуется

---

## 9. Контакты и поддержка

Проект создан в рамках практики.  
Если будут вопросы — смело пиши!
