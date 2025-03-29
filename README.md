# project_flower_shop
 
## 1. Общая информация

**FlowerShopBot** – это Telegram-бот, предназначенный для онлайн-продажи букетов в Красноярске. Бот позволяет:
- Выбрать букет по бюджету, событию (свадьба, день рождения и т. д.).
- Оформить заказ, указав имя, адрес, время доставки и телефон.
- При необходимости заказать консультацию флориста.
- Отправлять уведомления курьеру о новом заказе.

### Ключевые особенности

1. **Выбор «Другого повода»**: пользователь может ввести произвольный повод.  
2. **Запрос телефона**: при оформлении заказа и консультации бот проверяет номер.  
3. **Гибкая фильтрация по бюджету**: пользователь указывает примерную сумму, бот показывает подходящие букеты.  
4. **Фото из админки**: в Django-админке можно загружать фотографии букетов, которые бот потом отправляет в чат (при желании).  
5. **Отправка заказа курьеру**: после оформления заказа бот высылает данные курьеру (по Telegram chat_id).

---

## 2. Структура проекта

```
├── FlowerShopBot
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── README.md
├── bot
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── handlers
│   ├── logic
│   ├── main_bot.py
│   ├── management
│   ├── migrations
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── data
├── manage.py
├── media
│   ├── bouquets
│   └── compositions
├── requirements.txt
└── venv
```

**Пояснения**:

- **FlowerShopBot/** – Django-проект (файл `settings.py`, регистрация приложения `bot` в `INSTALLED_APPS`).
- **bot/** – пакет с кодом бота.
  - **main_bot.py** – точка запуска Telegram-бота (запускает `updater.start_polling()`).
  - **handlers/** – хендлеры (обработка команд/сообщений Telegram):
    - `start_handlers.py` – /start, главное меню (3 варианта: Букеты, Событие, Консультация).
    - `catalog_handlers.py` – выбор бюджета, листание букетов.
    - `order_handlers.py` – пошаговое оформление заказа (имя, адрес, время, телефон).
    - `consult_handlers.py` – запрос консультации (телефон).
    - `keyboards.py` – функции генерации клавиатур (InlineKeyboard).
  - **logic/** – бизнес-логика, работа с данными:
    - `data_access.py` – функции для чтения/записи из моделей Django (Bouquet, Order, Consultation).
    - `order_flow.py` – функции для оформления заказа (create_order, set_contact_info, confirm_order).
    - `consultation_flow.py` – функция request_consultation (проверка телефона + save_consultation).
    - `validators.py` – проверка/нормализация телефона и даты.

**.env** – хранит:
```
TELEGRAM_TOKEN=1234567:ABCdef...
COURIER_ID=987654321
FLORIST_ID=7777777
```
и т. д.

---

## 3. Основные файлы и их роль

### 3.1 main_bot.py

- Устанавливает настройки Django:
  ```python
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowerShopBot.settings')
  import django
  django.setup()
  ```
- Считывает `TELEGRAM_TOKEN` из `.env`.
- Регистрирует хендлеры (`dispatcher.add_handler(...)`) на разные `callback_data` и команды (`/start`).
- Запускает `updater.start_polling()` для прослушивания Telegram-событий.

### 3.2 start_handlers.py

- **handle_start**: обрабатывает `/start`, показывает клавиатуру с тремя пунктами: **Букеты**, **Событие**, **Консультация**.
- **handle_start_menu_selection**: когда пользователь нажимает «choose_bouquet» / «choose_event» / «request_consult», решает, куда дальше (показать бюджет, событие, или консультацию).
- **handle_event_selection**: когда пользователь выбрал «День рождения», «Свадьба» и т. д. (или «Другой повод»).
- **handle_messages**: главный обработчик текстовых сообщений (если пользователь вводит повод, телефон или идёт по шагам заказа).

### 3.3 consult_handlers.py

- **handle_consult_request**: при нажатии кнопки «Консультация» – спрашивает телефон.  
- **process_consult_request**: пользователь вводит телефон → вызывает `request_consultation` из `consultation_flow`.

### 3.4 catalog_handlers.py

- **handle_budget_selection**: пользователь выбрал бюджет – загружаем список букетов (через `start_bouquets`) и показываем первый.  
- **show_current_bouquet**: удаляет старое сообщение, отправляет новое (с фото и описанием) + кнопки «Заказать» / «Следующий букет».  
- **handle_catalog**: при нажатии «Следующий букет» – переключаем `current_bouquet` и снова вызываем `show_current_bouquet`.

### 3.5 order_handlers.py

- **handle_order_start**: пользователь нажал «Заказать» → начинаем пошаговый сбор данных (имя, адрес, дата, телефон).
- **process_order_step**: 4 шага:
  1. Имя  
  2. Адрес  
  3. Дата и время доставки  
  4. Телефон  
  Потом `create_order` + `set_contact_info` + `confirm_order`.
- **send_order_to_courier**: после подтверждения заказа – отправляет сообщение курьеру (ID берёт из `.env`).

### 3.6 data_access.py, order_flow.py, consultation_flow.py, validators.py

- **data_access.py**: 
  - `get_bouquets` – возвращает букеты по цене,  
  - `save_order` – создаёт Order в БД,  
  - `save_consultation` – создаёт Consultation.  
- **order_flow.py**: 
  - `create_order` – словарь заказа,  
  - `set_contact_info` – проверка телефона и даты,  
  - `confirm_order` – вызывает `save_order`.
- **consultation_flow.py**: 
  - `request_consultation` – проверяет телефон, сохраняет консультацию.
- **validators.py**: 
  - `normalize_phone` / `validate_phone`,  
  - `normalize_datetime` для даты (например «сегодня 14:00», «завтра 09:00», ISO-строка).

---

## 4. Установка и настройка

1. **Склонировать** репозиторий, зайти в папку.
2. **Создать виртуальное окружение** (Python 3.8+):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate.bat  # Windows
   ```
3. **Установить зависимости**:
   ```bash
   pip install -r requirements.txt
   ```
   Убедиться, что в `requirements.txt` есть `python-telegram-bot`, `django`, `python-dotenv`, `phonenumbers`.
4. **Создать .env** (если не создан):
   ```bash
   cp .env.example .env
   ```
   и вписать туда `TELEGRAM_TOKEN`, `COURIER_ID`, `FLORIST_ID` и т. д.
5. **Применить миграции** для Django (если нужно):
   ```bash
   python manage.py migrate
   ```
6. **Создать суперпользователя** (для доступа в админку):
   ```bash
   python manage.py createsuperuser
   ```
7. **Запустить Django-сервер** (для админки, если нужно):
   ```bash
   python manage.py runserver
   ```
8. **Запустить бота**:
   ```bash
   cd project_flower_shop
   python -m bot.main_bot
   ```
   Если всё верно, консоль покажет `Start polling...`.

---

## 5. Как пользоваться

1. **Запустить бота** (см. выше).
2. **Войти** в Telegram, найти своего бота по `@YourBotName`, нажать `/start`.
3. Бот предложит три кнопки:
   1. **Букеты** (choose_bouquet) – сразу спрашивает бюджет, затем показывает букеты.  
   2. **Событие** (choose_event) – спрашивает конкретное событие (День рождения, Свадьба…), а потом бюджет.  
   3. **Консультация** (request_consult) – сразу спрашивает телефон, сохраняет в Consultation.  
4. **Выбрать** нужный пункт, следовать инструкциям бота: ввести имя, адрес, время доставки, телефон.  
5. **Заказ** подтверждается, бот отправляет заказ курьеру, а тебе пишет «Заказ оформлен!».
6. **Проверить** в админке (http://127.0.0.1:8000/admin/) в моделях Order и Consultation, что всё сохранилось.

---

## 6. Дополнительные замечания

- **Фото** букетов: в админке у модели `Bouquet` можно загрузить `photo`. Бот при показе букета (в `show_current_bouquet`) проверяет `bouquet_obj.photo`. Если оно есть – удаляет старое сообщение и отправляет новое с фото+caption.
- **Часовой пояс**: время доставки хранится и показывается в Asia/Krasnoyarsk (или как настроено). Убедись, что `TIME_ZONE = 'Asia/Krasnoyarsk'` в настройках, либо что `order_flow`/`data_access` делают make_aware(...) корректно.
- **Редактирование** vs. **Удаление** сообщений: чтобы избежать ошибки «There is no text in the message to edit», мы удаляем старое сообщение (`query.delete_message()`) и отправляем новое.  

---

## 8. Лицензия

