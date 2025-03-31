import os
from telegram import Update
from telegram.ext import CallbackContext
from bot.logic.consultation_flow import request_consultation
from bot.handlers.catalog_handlers import show_current_bouquet
from bot.logic.order_flow import start_bouquets
from bot.message_tools import safe_delete_message
from bot.logging_tools import log_validation_error, log_unexpected_error
from bot.exceptions import InvalidPhoneError


def handle_consult_request(update: Update, context: CallbackContext):
    """
    Обработка кнопки 'Консультация'.
    Запрашиваем у пользователя номер телефона.
    """
    query = update.callback_query
    query.answer()
    safe_delete_message(query)
    context.bot.send_message(
        chat_id=query.message.chat_id,
        text="📱 Укажите номер телефона для связи с флористом (в течение 20 минут вам перезвонят):"
    )
    context.user_data["awaiting_phone"] = True

def process_consult_request(update: Update, context: CallbackContext):
    phone = update.message.text.strip()
    user = update.effective_user

    try:
        consultation_data = request_consultation(
            phone=phone,
            user_id=user.id,
            name=user.full_name or user.username or "(без имени)"
        )

        florist_id = os.getenv("FLORIST_ID")
        if florist_id:
            context.bot.send_message(
                chat_id=florist_id,
                text=f"📞 Новая консультация:\n"
                     f"Имя: {consultation_data['name']}\n"
                     f"Телефон: {consultation_data['phone']}"
            )

        update.message.reply_text(
            "🌸 Флорист скоро свяжется с вами!\n"
            "А пока можете присмотреть что-нибудь из готовой коллекции 👇"
        )

        context.user_data.pop("awaiting_phone", None)
        context.user_data.pop("order_step", None)
        context.user_data.pop("order_data", None)

        bouquets = start_bouquets()
        if bouquets:
            context.user_data["bouquets"] = bouquets
            context.user_data["current_bouquet"] = 0
            show_current_bouquet(update, context)

    except InvalidPhoneError as e:
        log_validation_error("Неверный номер телефона", e)
        update.message.reply_text("❌ Неверный формат номера. Пример: +79991234567")

    except Exception as e:
        log_unexpected_error("Неожиданная ошибка в process_consult_request", e)




        
