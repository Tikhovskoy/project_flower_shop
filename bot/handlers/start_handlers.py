from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from .keyboards import generate_start_menu, generate_event_keyboard, generate_budget_keyboard
from .consult_handlers import process_consult_request
from .order_handlers import process_order_step

def handle_start(update: Update, context: CallbackContext):
    """
    /start – показываем главное меню с тремя вариантами:
    1) Букеты
    2) Событие
    3) Консультация
    """
    update.message.reply_text(
        text="Привет! Что вы хотите выбрать?",
        reply_markup=generate_start_menu()
    )

def handle_start_menu_selection(update: Update, context: CallbackContext):
    """Обработка выбора главного меню: choose_bouquet, choose_event, request_consult."""
    query = update.callback_query
    data = query.data

    if data == "choose_bouquet":
        context.user_data.pop("event", None)
        query.edit_message_text(
            text="💰 На какую сумму рассчитываете?",
            reply_markup=generate_budget_keyboard()
        )
    elif data == "choose_event":
        query.edit_message_text(
            text="🎉 К какому событию готовимся?",
            reply_markup=generate_event_keyboard()
        )
    elif data == "request_consult":
        from .consult_handlers import handle_consult_request
        handle_consult_request(update, context)
    else:
        query.edit_message_text("Неизвестная команда.")

def handle_event_selection(update: Update, context: CallbackContext):
    """
    Когда пользователь выбрал конкретное событие (birthday, wedding, school, no_reason, custom)
    """
    query = update.callback_query
    data = query.data

    if data == "custom":
        query.edit_message_text("📝 Напишите ваш повод:")
        context.user_data["awaiting_event_custom"] = True
    else:
        context.user_data["event"] = data
        query.edit_message_text(
            text="💰 На какую сумму рассчитываете?",
            reply_markup=generate_budget_keyboard()
        )

def handle_messages(update: Update, context: CallbackContext):
    """
    Главный обработчик текстовых сообщений:
      - Если пользователь вводит «другой повод»,
      - Если вводит телефон для консультации,
      - Если находится в процессе оформления заказа.
    """
    if context.user_data.get("awaiting_event_custom"):
        context.user_data["event"] = update.message.text
        del context.user_data["awaiting_event_custom"]

        from .keyboards import generate_budget_keyboard
        update.message.reply_text(
            text="💰 На какую сумму рассчитываете?",
            reply_markup=generate_budget_keyboard()
        )
    elif context.user_data.get("awaiting_phone"):
        process_consult_request(update, context)
    elif "order_step" in context.user_data:
        process_order_step(update, context)
    else:
        update.message.reply_text("Я вас не понял. Нажмите /start, чтобы начать заново.")
