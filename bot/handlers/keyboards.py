from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def generate_event_keyboard():
    """
    Возвращает клавиатуру для выбора события.
    """
    keyboard = [
        [InlineKeyboardButton("День рождения", callback_data="birthday")],
        [InlineKeyboardButton("Свадьба", callback_data="wedding")],
        [InlineKeyboardButton("В школу", callback_data="school")],
        [InlineKeyboardButton("Без повода", callback_data="no_reason")],
        [InlineKeyboardButton("Другой повод", callback_data="custom")]
    ]
    return InlineKeyboardMarkup(keyboard)

def generate_budget_keyboard():
    """
    Возвращает клавиатуру для выбора бюджета.
    """
    keyboard = [
        [InlineKeyboardButton("~500", callback_data="500")],
        [InlineKeyboardButton("~1000", callback_data="1000")],
        [InlineKeyboardButton("~2000", callback_data="2000")],
        [InlineKeyboardButton("Больше", callback_data="more")],
        [InlineKeyboardButton("Не важно", callback_data="any")]
    ]
    return InlineKeyboardMarkup(keyboard)
