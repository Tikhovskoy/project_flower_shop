from telegram.error import TelegramError
from telegram.ext import CallbackContext

from bot.logging_tools import log_unexpected_error

ERROR_REPLY = "❌ Что-то пошло не так. Попробуйте ещё раз или нажмите /start."


def handle_error(update, context: CallbackContext) -> None:
    """Общий обработчик: сюда попадает всё, что не поймали конкретные хендлеры.

    Пишет ошибку с трассировкой в лог и, если есть куда, извиняется перед пользователем.
    """
    log_unexpected_error("Необработанная ошибка в обработчике", context.error)

    message = getattr(update, "effective_message", None)
    if message is None:
        return
    try:
        message.reply_text(ERROR_REPLY)
    except TelegramError as error:
        log_unexpected_error("Не удалось отправить сообщение об ошибке", error)
