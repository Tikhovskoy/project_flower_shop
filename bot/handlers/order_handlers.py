from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from bot.logic.order_flow import create_order, set_contact_info, confirm_order

def handle_order_start(update: Update, context: CallbackContext):
    """Пользователь нажал 'Заказать' – начинаем оформление заказа, запрашиваем имя."""
    query = update.callback_query
    query.message.reply_text("Введите ваше имя:")
    context.user_data["order_step"] = 0

def process_order_step(update: Update, context: CallbackContext):
    """
    Пошаговая обработка данных заказа:
      Шаг 0: Имя
      Шаг 1: Адрес доставки
      Шаг 2: Дата и время доставки
      Шаг 3: Выбор добавления открытки (inline кнопки)
      Шаг 4: Ввод текста открытки (если выбран "Да")
      Шаг 5: Ввод номера телефона
    """
    user_data = context.user_data
    step = user_data.get("order_step", 0)
    text = update.message.text.strip()

    if step == 0:
        user_data["name"] = text
        update.message.reply_text("Введите адрес доставки:")
        user_data["order_step"] = 1

    elif step == 1:
        user_data["address"] = text
        update.message.reply_text(
            "Укажите дату и время доставки.\n"
            "Примеры форматов:\n"
            "- 27.03.2025 14:00\n"
            "- сегодня 14:00\n"
            "- завтра 09:00"
        )
        user_data["order_step"] = 2

    elif step == 2:
        user_data["datetime"] = text
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data="add_card_yes"),
             InlineKeyboardButton("Нет", callback_data="add_card_no")]
        ])
        update.message.reply_text("Хотите добавить открытку?", reply_markup=keyboard)
        user_data["order_step"] = 3

    elif step == 3:
        update.message.reply_text("Пожалуйста, нажмите одну из кнопок для выбора открытки.")
        return

    elif step == 4:
        user_data["card_text"] = text
        update.message.reply_text("Введите ваш номер телефона (в любом формате):")
        user_data["order_step"] = 5

    elif step == 5:
        user_data["phone"] = text
        try:
            idx = user_data["current_bouquet"]
            chosen_bouquet = user_data["bouquets"][idx]
            order_data = create_order(chosen_bouquet)
            order_data = set_contact_info(
                order_data,
                user_data["name"],
                user_data["address"],
                user_data["phone"],
                user_data["datetime"]
            )
            if "card_text" in user_data:
                order_data["card_text"] = user_data["card_text"]
            order_data["status"] = "confirmed"
            confirm_order(order_data)
            send_order_to_courier(context, order_data)
            update.message.reply_text("✅ Заказ оформлен!")
            user_data.clear()
        except ValueError as e:
            update.message.reply_text(
                f"❌ {str(e)}\nПовторите ввод данных или введите /start для начала заново."
            )
    else:
        user_data.clear()

def handle_card_choice(update: Update, context: CallbackContext):
    """
    Обработка выбора добавления открытки.
    Если пользователь нажал "Да" (callback_data="add_card_yes"), переводим его на шаг 4.
    Если "Нет" (callback_data="add_card_no") – сразу переходим к вводу номера телефона (шаг 5).
    """
    query = update.callback_query
    data = query.data
    user_data = context.user_data

    if data == "add_card_yes":
        query.edit_message_text("Введите текст открытки:")
        user_data["order_step"] = 4
    elif data == "add_card_no":
        user_data.pop("card_text", None)
        query.edit_message_text("Введите ваш номер телефона (в любом формате):")
        user_data["order_step"] = 5
    else:
        query.edit_message_text("Неизвестный выбор. Попробуйте ещё раз.")

def send_order_to_courier(context: CallbackContext, order_data: dict):
    """
    Отправка сообщения о новом заказе курьеру.
    """
    from bot.handlers.handlers_config import COURIER_ID
    if not COURIER_ID:
        print("COURIER_ID не задан, сообщение курьеру не отправлено.")
        return

    text = (
        "🚚 Новый заказ!\n"
        f"Имя: {order_data['customer_name']}\n"
        f"Адрес: {order_data['address']}\n"
        f"Дата: {order_data['delivery_time']}\n"
        f"Телефон: {order_data['phone']}\n"
        f"Букет: {order_data['bouquet_name']} (Цена: {order_data['price']}₽)\n"
    )
    context.bot.send_message(chat_id=COURIER_ID, text=text)
