from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from django.conf import settings
from bot.logic.order_flow import start_bouquets, start_compositions
from bot.message_tools import safe_delete_message

def handle_budget_selection(update: Update, context: CallbackContext):
    """Обработка выбора бюджета."""
    query = update.callback_query
    data = query.data

    if data == "any":
        min_price, max_price = 0, 9999999
    elif data == "more":
        min_price, max_price = 2000, 9999999
    else:
        budget = int(data)
        min_price = max(0, budget - 500)
        max_price = budget

    event = context.user_data.get("event")
    if event and event.lower() in ["wedding", "march8", "teacher", "no_reason", "birthday", "school", "custom"]:
        bouquets = start_compositions(event)
    else:
        bouquets = start_bouquets(min_price, max_price)

    if not bouquets:
        query.edit_message_text("😔 Нет букетов в этом диапазоне.")
        return

    context.user_data["bouquets"] = bouquets
    context.user_data["current_bouquet"] = 0

    show_current_bouquet(update, context)

def show_current_bouquet(update: Update, context: CallbackContext):
    """Показывает букет — работает и после callback, и после text-сообщения."""
    chat_id = None
    if update.callback_query:
        query = update.callback_query
        chat_id = query.message.chat_id
        safe_delete_message(query)
    elif update.message:
        chat_id = update.message.chat_id

    if not chat_id:
        return

    idx = context.user_data["current_bouquet"]
    bouquet = context.user_data["bouquets"][idx]

    poetic = bouquet.poetic_text.strip() if getattr(bouquet, "poetic_text", "") else ""
    poetic = f"<i>{poetic}</i>\n\n" if poetic else ""

    caption_text = (
        f"<b>{bouquet.name}</b>\n"
        f"<i>Цена:</i> {bouquet.price} ₽\n\n"
        f"{poetic}"
        f"{bouquet.description or 'Описание отсутствует.'}\n\n"
        "<b>Хотите заказать этот букет или посмотреть следующий?</b>"
    )

    buttons = [
        [InlineKeyboardButton("✅ Заказать", callback_data="start_order")],
        [InlineKeyboardButton("➡️ Следующий букет", callback_data="show_catalog")],
        [InlineKeyboardButton("📞 Консультация", callback_data="request_consult")]
    ]
    markup = InlineKeyboardMarkup(buttons)

    if bouquet.photo:
        photo_path = f"{settings.MEDIA_ROOT}/{bouquet.photo.name}"
        with open(photo_path, "rb") as photo:
            context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption_text,
                parse_mode="HTML",
                reply_markup=markup
            )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text=caption_text,
            parse_mode="HTML",
            reply_markup=markup
        )

def handle_catalog(update: Update, context: CallbackContext):
    """Показ следующего букета из списка."""
    context.user_data["current_bouquet"] += 1
    bouquets = context.user_data["bouquets"]
    context.user_data["current_bouquet"] %= len(bouquets)
    show_current_bouquet(update, context)
