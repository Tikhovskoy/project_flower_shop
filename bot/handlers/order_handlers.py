import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from bot.logic.order_flow import create_order, add_card_text, set_contact_info, confirm_order
from bot.message_tools import safe_delete_message
from bot.logging_tools import log_validation_error, log_unexpected_error
from bot.exceptions import InvalidPhoneError, InvalidDateTimeError, OrderSaveError
from bot.logic.validators import normalize_datetime


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
    chat_id = query.message.chat_id

    safe_delete_message(query)

    if choice == "add_card_yes":
        context.user_data["order_step"] = "card_text"
        context.bot.send_message(chat_id=chat_id, text="✏️ Введите текст открытки:")
    else:
        context.user_data["order_step"] = "name"
        context.bot.send_message(chat_id=chat_id, text="👤 Как вас зовут?")


def process_order_step(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    step = context.user_data.get("order_step")
    order_data = context.user_data.get("order_data")

    try:
        if step == "card_text":
            add_card_text(order_data, text)
            context.user_data["order_step"] = "name"
            update.message.reply_text("👤 Как вас зовут?")
            return

        elif step == "name":
            context.user_data["customer_name"] = text
            context.user_data["order_step"] = "address"
            update.message.reply_text("🏡 Укажите адрес доставки:")
            return

        elif step == "address":
            context.user_data["address"] = text
            context.user_data["order_step"] = "delivery_time"
            update.message.reply_text("📅 Укажите дату и время доставки (например: 2025-03-27 14:00):")
            return

        elif step == "delivery_time":
            try:
                normalized_time = normalize_datetime(text)
                if not normalized_time:
                    raise InvalidDateTimeError("Неверный формат даты. Пример: 2025-03-27 14:00")

                context.user_data["delivery_time"] = normalized_time
                context.user_data["order_step"] = "phone"
                update.message.reply_text("📞 Укажите номер телефона:")
                return

            except InvalidDateTimeError as e:
                log_validation_error("Ошибка даты доставки", e)
                update.message.reply_text(
                    "❌ Неверный формат даты. Пример: 2025-03-27 14:00\nПожалуйста, повторите ввод."
                )
                return

        elif step == "phone":
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
            return

        context.user_data.clear()
        update.message.reply_text("⚠️ Неожиданный шаг. Попробуйте /start")
        return

    except (InvalidPhoneError, InvalidDateTimeError) as e:
        log_validation_error(f"Ошибка в process_order_step (шаг {step})", str(e))
        update.message.reply_text(f"❌ {e}\nПожалуйста, повторите ввод.")
        return

    except OrderSaveError as e:
        log_unexpected_error("Ошибка сохранения заказа", str(e))
        update.message.reply_text("⚠️ Не удалось сохранить заказ. Попробуйте позже.")
        return

    except Exception as e:
        log_unexpected_error(f"Неожиданная ошибка в process_order_step (шаг {step})", str(e))
        update.message.reply_text("❌ Что-то пошло не так. Попробуйте позже.")
        return


def send_order_to_courier(context: CallbackContext, order_data: dict):
    """Отправляет заказ курьеру."""
    courier_id = os.getenv("COURIER_ID")
    if not courier_id:
        log_unexpected_error("Отсутствует COURIER_ID в .env", Exception("COURIER_ID is not set"))
        return

    text = (
        "🚚 Новый заказ!\n\n"
        f"💐 Букет: {order_data['bouquet_name']}\n"
        f"💰 Цена: {order_data['price']}₽\n"
        f"👤 Получатель: {order_data['customer_name']}\n"
        f"🏡 Адрес: {order_data['delivery_address']}\n"
        f"📅 Время доставки: {order_data['delivery_time'].strftime('%d.%m %H:%M')}\n"
        f"📞 Телефон: {order_data['phone_number']}\n"
    )

    if order_data.get("card_text"):
        text += f"\n💌 Открытка: {order_data['card_text']}"

    context.bot.send_message(chat_id=courier_id, text=text)
