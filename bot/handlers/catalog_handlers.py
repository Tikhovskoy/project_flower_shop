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
        bouquets = start_compositions(event, min_price, max_price)
    else:
        bouquets = start_bouquets(min_price, max_price)

    if not bouquets:
        query.edit_message_text("😔 Нет букетов в этом диапазоне.")
        return

    context.user_data["bouquets"] = bouquets
    context.user_data["current_bouquet"] = 0

    show_current_bouquet(update, context)


def handle_full_collection(update: Update, context: CallbackContext):
    """Показывает всю коллекцию букетов по текущей категории без ограничений по бюджету."""
    query = update.callback_query
    query.answer()

    event = context.user_data.get("event")

    if event and event.lower() in ["wedding", "no_reason", "birthday", "school", "custom"]:
        bouquets = start_compositions(event, min_price=0, max_price=9999999)
    else:
        bouquets = start_bouquets(min_price=0, max_price=9999999)

    if not bouquets:
        query.edit_message_text("😔 Нет букетов в коллекции.")
        return

    context.user_data["bouquets"] = bouquets
    context.user_data["current_bouquet"] = 0

    show_current_bouquet(update, context)


def show_current_bouquet(update: Update, context: CallbackContext):
    """Показывает букет с описанием и дополнительными кнопками."""
    chat_id = None
    if update.callback_query:
        query = update.callback_query
        chat_id = query.message.chat_id
        safe_delete_message(query)
    elif update.message:
        chat_id = update.message.chat_id

    if not chat_id:
        return

    idx = context.user_data.get("current_bouquet", 0)
    bouquets = context.user_data.get("bouquets", [])

    if not bouquets:
        context.bot.send_message(chat_id=chat_id, text="⚠️ Нет доступных букетов.")
        return

    bouquet = bouquets[idx % len(bouquets)]

    poetic = bouquet.poetic_text.strip() if getattr(bouquet, "poetic_text", "") else ""
    poetic = f"<i>{poetic}</i>\n\n" if poetic else ""

    caption_text = (
        f"<b>{bouquet.name}</b>\n"
        f"<i>Цена:</i> {bouquet.price} ₽\n\n"
        f"{poetic}"
        f"{bouquet.description or 'Описание отсутствует.'}"
    )

    main_buttons = [
        [InlineKeyboardButton("✅ Заказать букет", callback_data="start_order")],
        [InlineKeyboardButton("➡️ Следующий букет", callback_data="show_catalog")],
    ]

    bottom_buttons = [
        [InlineKeyboardButton("🌸 Посмотреть всю коллекцию", callback_data="show_full_collection")],
        [InlineKeyboardButton("📞 Заказать консультацию", callback_data="request_consult")]
    ]

    if bouquet.photo:
        photo_path = f"{settings.MEDIA_ROOT}/{bouquet.photo.name}"
        with open(photo_path, "rb") as photo:
            context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(main_buttons)
            )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text=caption_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(main_buttons)
        )

    context.bot.send_message(
        chat_id=chat_id,
        text="<b>Хотите что-то еще более уникальное?</b> Подберите другой букет из нашей коллекции или закажите консультацию флориста",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(bottom_buttons)
    )


def handle_catalog(update: Update, context: CallbackContext):
    """Показ следующего букета из списка."""
    context.user_data["current_bouquet"] += 1
    bouquets = context.user_data["bouquets"]
    context.user_data["current_bouquet"] %= len(bouquets)
    show_current_bouquet(update, context)
