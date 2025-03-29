from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from bot.logic.order_flow import start_bouquets, start_compositions

def handle_budget_selection(update: Update, context: CallbackContext):
    """Обработка выбора бюджета"""
    query = update.callback_query
    data = query.data 

    if data == "any":
        min_price, max_price = 0, 9999999
    else:
        budget = int(data)
        min_price = max(0, budget - 500)
        max_price = budget

    event = context.user_data.get("event")
    if event in ["march8", "wedding", "teacher", "no_reason"]:
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
    """
    Отображает текущий букет:
      - Удаляет старое сообщение.
      - Отправляет новое сообщение с информацией о букете.
    """
    query = update.callback_query
    idx = context.user_data["current_bouquet"]
    bouquet_obj = context.user_data["bouquets"][idx]

    caption_text = (
        f"💐 {bouquet_obj.name}\n"
        f"Цена: {bouquet_obj.price} ₽\n"
        f"{bouquet_obj.description or ''}\n\n"
        "Хотите заказать этот букет или посмотреть следующий?"
    )

    try:
        query.delete_message()
    except Exception:
        pass

    if bouquet_obj.photo:
        photo_path = bouquet_obj.photo.path
        with open(photo_path, 'rb') as f:
            context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=f,
                caption=caption_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Заказать", callback_data="start_order")],
                    [InlineKeyboardButton("➡️ Следующий букет", callback_data="show_catalog")]
                ])
            )
    else:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=caption_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Заказать", callback_data="start_order")],
                [InlineKeyboardButton("➡️ Следующий букет", callback_data="show_catalog")]
            ])
        )

def handle_catalog(update: Update, context: CallbackContext):
    """Показ следующего букета в каталоге."""
    context.user_data["current_bouquet"] += 1
    bouquets = context.user_data["bouquets"]
    context.user_data["current_bouquet"] %= len(bouquets)
    show_current_bouquet(update, context)
