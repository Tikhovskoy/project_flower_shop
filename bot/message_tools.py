from contextlib import suppress

from telegram.error import TelegramError


def safe_delete_message(query):
    """Удаляет сообщение с кнопкой; ошибки Telegram (уже удалено, нет прав, сеть) не критичны."""
    if query.message:
        with suppress(TelegramError):
            query.message.delete()
