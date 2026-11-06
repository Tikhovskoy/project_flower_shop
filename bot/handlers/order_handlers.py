from django.conf import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from bot.exceptions import InvalidDateTimeError, InvalidPhoneError, OrderSaveError
from bot.logging_tools import log_unexpected_error, log_validation_error
from bot.logic.order_draft import OrderDraft
from bot.logic.order_flow import confirm_order, create_order
from bot.logic.validators import normalize_datetime
from bot.message_tools import safe_delete_message


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
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Да", callback_data="add_card_yes")],
                [InlineKeyboardButton("Нет", callback_data="add_card_no")],
            ]
        ),
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
            order_data.add_card_text(text)
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
            update.message.reply_text(
                "📅 Укажите дату и время доставки (например: 2025-03-27 14:00):"
            )
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
            order = order_data.set_contact_info(
                customer_name=context.user_data["customer_name"],
                address=context.user_data["address"],
                phone=text,
                delivery_time=context.user_data["delivery_time"],
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

    except OrderSaveError:
        update.message.reply_text("⚠️ Не удалось сохранить заказ. Попробуйте позже.")
        return


def send_order_to_courier(context: CallbackContext, order: OrderDraft):
    """Отправляет заказ курьеру."""
    courier_id = settings.COURIER_ID
    if not courier_id:
        log_unexpected_error("Отсутствует COURIER_ID в .env", Exception("COURIER_ID is not set"))
        return

    context.bot.send_message(chat_id=courier_id, text=order.courier_message())
