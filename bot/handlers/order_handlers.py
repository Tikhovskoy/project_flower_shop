import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from bot.logic.order_flow import create_order, add_card_text, set_contact_info, confirm_order
from bot.message_tools import safe_delete_message
from bot.logic.validators import normalize_datetime
from bot.handlers.handlers_config import COURIER_ID


def handle_order_start(update: Update, context: CallbackContext):
    """Начинаем оформление заказа — спрашиваем про открытку."""
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id

    idx = context.user_data.get("current_bouquet", 0)
    bouquet = context.user_data["bouquets"][idx]
    context.user_data["order_data"] = create_order(bouquet)
    context.user_data["order_step"] = "card"

    safe_delete_message(query)

    context.bot.send_message(
        chat_id=chat_id,
        text="💌 Хотите добавить открытку к букету?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data="add_card_yes")],
            [InlineKeyboardButton("Нет", callback_data="add_card_no")]
        ])
    )

def handle_card_choice(update: Update, context: CallbackContext):
    """Обработка выбора: нужна ли открытка."""
    query = update.callback_query
    choice = query.data
    if choice == "add_card_yes":
        context.user_data["order_step"] = "card_text"
        query.edit_message_text("✏️ Введите текст открытки:")
    else:
        context.user_data["order_step"] = "name"
        query.edit_message_text("👤 Как вас зовут?")

def process_order_step(update: Update, context: CallbackContext):
    """Пошаговая обработка оформления заказа."""
    text = update.message.text.strip()
    step = context.user_data.get("order_step")
    order_data = context.user_data.get("order_data")

    if step == "card_text":
        add_card_text(order_data, text)
        context.user_data["order_step"] = "name"
        update.message.reply_text("👤 Как вас зовут?")

    elif step == "name":
        context.user_data["customer_name"] = text
        context.user_data["order_step"] = "address"
        update.message.reply_text("🏡 Укажите адрес доставки:")

    elif step == "address":
        context.user_data["address"] = text
        context.user_data["order_step"] = "delivery_time"
        update.message.reply_text("📅 Укажите дату и время доставки (например: Сегодня 15:00):")

    elif step == "delivery_time":
        from bot.logic.validators import normalize_datetime
        normalized_time = normalize_datetime(text)
        if normalized_time is None:
            update.message.reply_text("❌ Неверный формат времени доставки. Пример: '2025-03-27T14:00'. Пожалуйста, повторите ввод даты и времени:")
            return  
        context.user_data["delivery_time"] = normalized_time
        context.user_data["order_step"] = "phone"
        update.message.reply_text("📞 Укажите номер телефона:")

    elif step == "phone":
        try:
            order = set_contact_info(
                order_data,
                customer_name=context.user_data["customer_name"],
                address=context.user_data["address"],
                phone=text,
                delivery_time=context.user_data["delivery_time"]
            )
            confirm_order(order)
            send_order_to_courier(context, order)

            update.message.reply_text("✅ Заказ подтверждён! Курьер скоро с вами свяжется.")
            context.user_data.clear()
        except ValueError as e:
            update.message.reply_text(f"❌ {e}\nПожалуйста, повторите ввод номера:")
    else:
        context.user_data.clear()

def send_order_to_courier(context: CallbackContext, order_data: dict):
    """Отправляет заказ курьеру."""
    import os
    COURIER_ID = os.getenv("COURIER_ID")
    text = (
        "🚚 Новый заказ!\n\n"
        f"💐 Букет: {order_data['bouquet_name']}\n"
        f"💰 Цена: {order_data['price']}₽\n"
        f"👤 Получатель: {order_data['customer_name']}\n"
        f"🏡 Адрес: {order_data['address']}\n"
        f"📅 Время доставки: {order_data['delivery_time'].strftime('%d.%m %H:%M')}\n"
        f"📞 Телефон: {order_data['phone']}\n"
    )
    if order_data.get("card_text"):
        text += f"\n💌 Открытка: {order_data['card_text']}"
    context.bot.send_message(chat_id=COURIER_ID, text=text)
