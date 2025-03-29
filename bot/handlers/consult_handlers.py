import os
from telegram import Update
from telegram.ext import CallbackContext
from bot.logic.consultation_flow import request_consultation

def handle_consult_request(update: Update, context: CallbackContext):
    """Нажали 'Консультация'"""
    query = update.callback_query
    query.edit_message_text("📱 Укажите номер телефона:")
    context.user_data["awaiting_phone"] = True

def process_consult_request(update: Update, context: CallbackContext):
    """Пользователь вводит телефон для консультации"""
    phone = update.message.text.strip()
    try:
        consultation_data = request_consultation(phone, user_id=update.effective_user.id)
        
        florist_id = os.getenv("FLORIST_ID")
        if florist_id:
            context.bot.send_message(
                chat_id=florist_id,
                text=f"📞 Новая консультация:\nТелефон: {consultation_data['phone']}"
            )
        
        update.message.reply_text("🌸 Флорист скоро свяжется с вами!")
        context.user_data.pop("awaiting_phone", None)
    except ValueError as e:
        update.message.reply_text(
            f"❌ {e}\nПожалуйста, введите корректный номер."
        )
