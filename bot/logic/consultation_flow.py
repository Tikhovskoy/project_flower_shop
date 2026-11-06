from django.db import DatabaseError

from bot.exceptions import ConsultationSaveError, InvalidPhoneError
from bot.logging_tools import log_unexpected_error, log_validation_error

from .data_access import save_consultation
from .validators import normalize_phone


def request_consultation(phone: str, user_id: int, name: str = "(аноним)") -> dict:
    """
    Принимает номер телефона, проверяет и сохраняет заявку на консультацию.
    """
    try:
        normalized_phone = normalize_phone(phone)
    except InvalidPhoneError as e:
        log_validation_error("Ошибка валидации номера в request_consultation", e)
        raise

    consultation_data = {
        "phone": normalized_phone,
        "user_id": user_id,
        "name": name,
        "status": "new",
    }

    try:
        save_consultation(consultation_data)
    except DatabaseError as e:
        log_unexpected_error("Ошибка сохранения консультации в request_consultation", e)
        raise ConsultationSaveError("Не удалось сохранить заявку.") from e

    return consultation_data
