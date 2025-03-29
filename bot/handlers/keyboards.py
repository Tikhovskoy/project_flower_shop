from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def generate_start_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Букеты", callback_data="choose_bouquet")],
        [InlineKeyboardButton("Событие", callback_data="choose_event")],
        [InlineKeyboardButton("Консультация", callback_data="request_consult")]
    ])

def generate_event_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("8 марта", callback_data="march8")],
        [InlineKeyboardButton("Для свадьбы", callback_data="wedding")],
        [InlineKeyboardButton("Для учителя", callback_data="teacher")],
        [InlineKeyboardButton("Без повода", callback_data="no_reason")],
        [InlineKeyboardButton("Другой повод", callback_data="custom")]
    ])

def generate_budget_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("~500 ₽", callback_data="500")],
        [InlineKeyboardButton("~1000 ₽", callback_data="1000")],
        [InlineKeyboardButton("~2000 ₽", callback_data="2000")],
        [InlineKeyboardButton("Не важно", callback_data="any")]
    ])
