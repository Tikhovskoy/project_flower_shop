from telegram import Update
from telegram.ext import CallbackContext
from .keyboards import generate_event_keyboard, generate_budget_keyboard
from bot.message_tools import safe_delete_message
from bot.handlers.order_handlers import process_order_step
from bot.handlers.consult_handlers import process_consult_request



def handle_start(update: Update, context: CallbackContext):
    """
    Обработка команды /start.
    Отправляет сообщение с выбором события.
    """
    welcome_text = "К какому событию готовимся? Выберите один из вариантов, либо укажите свой."
    update.message.reply_text(
        text=welcome_text,
        reply_markup=generate_event_keyboard()
    )

def handle_event_selection(update: Update, context: CallbackContext):
    """
    Обработка выбора события.
    Если выбран 'custom', просим ввести текст;
    иначе – сохраняем выбранное событие и отправляем клавиатуру выбора бюджета.
    """
    query = update.callback_query
    data = query.data
    safe_delete_message(query)
    if data == "custom":
        query.message.reply_text("📝 Напишите ваш повод:")
        context.user_data["awaiting_custom_event"] = True
    else:
        context.user_data["event"] = data
        query.message.reply_text(
            text="💰 На какую сумму рассчитываете?",
            reply_markup=generate_budget_keyboard()
        )

def handle_messages(update: Update, context: CallbackContext):
    """
    Главный обработчик текстовых сообщений.
    Приоритет: сначала проверяем, ожидается номер телефона, затем – другие состояния.
    """
    if context.user_data.get("awaiting_phone"):
        process_consult_request(update, context)
    elif context.user_data.get("awaiting_custom_event"):
        custom_event = update.message.text.strip()
        context.user_data["event"] = custom_event
        context.user_data.pop("awaiting_custom_event", None)
        update.message.reply_text(
            text="💰 На какую сумму рассчитываете?",
            reply_markup=generate_budget_keyboard()
        )
    elif "order_step" in context.user_data:
        process_order_step(update, context)
    else:
        update.message.reply_text("Я вас не понял. Нажмите /start, чтобы начать заново.")

