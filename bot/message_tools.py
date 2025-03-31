from telegram.error import BadRequest

def safe_delete_message(query):
    """Пытается удалить сообщение, игнорируя ошибки."""
    try:
        if query.message:
            query.message.delete()
    except BadRequest:
        pass
    except Exception:
        pass
