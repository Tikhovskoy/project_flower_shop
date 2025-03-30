import os
from telegram import Update
from telegram.ext import CallbackContext
from bot.logic.consultation_flow import request_consultation
from bot.handlers.catalog_handlers import show_current_bouquet
from bot.logic.order_flow import start_bouquets
from bot.message_tools import safe_delete_message


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
    """
    Обработка ввода телефона для консультации.
    Если всё хорошо — уведомляем флориста и предлагаем посмотреть коллекцию.
    """
    phone = update.message.text.strip()
    try:
        consultation_data = request_consultation(phone, user_id=update.effective_user.id)
        florist_id = os.getenv("FLORIST_ID")
        if florist_id:
            context.bot.send_message(
                chat_id=florist_id,
                text=f"📞 Новая консультация:\nТелефон: {consultation_data['phone']}"
            )
        update.message.reply_text(
            "🌸 Флорист скоро свяжется с вами!\n"
            "А пока можете присмотреть что-нибудь из готовой коллекции 👇"
        )
        bouquets = start_bouquets()
        if bouquets:
            context.user_data["bouquets"] = bouquets
            context.user_data["current_bouquet"] = 0
            show_current_bouquet(update, context)
        context.user_data.pop("awaiting_phone", None)
    except ValueError as e:
        update.message.reply_text(
            f"❌ {e}\nПожалуйста, введите корректный номер."
        )