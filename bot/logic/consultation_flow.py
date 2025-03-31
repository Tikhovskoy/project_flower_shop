from .data_access import save_consultation
from .validators import validate_phone, normalize_phone
from phonenumbers import NumberParseException
from bot.logging_tools import log_validation_error, log_unexpected_error
from bot.exceptions import InvalidPhoneError


def request_consultation(phone: str, user_id: int, name: str = "(аноним)") -> dict:
    """
    Принимает номер телефона, проверяет и сохраняет заявку на консультацию.
    """
    try:
        normalized_phone = normalize_phone(phone)
        if not validate_phone(normalized_phone):
            raise InvalidPhoneError("❌ Неверный формат номера телефона. Пример: +79991234567")

        consultation_data = {
            "phone": normalized_phone,
            "user_id": user_id,
            "name": name,
            "status": "new"
        }

        save_consultation(consultation_data)
        return consultation_data

    except InvalidPhoneError as e:
        log_validation_error("Ошибка валидации номера в request_consultation", e)
        raise

    except Exception as e:
        log_unexpected_error("Неожиданная ошибка в request_consultation", e)
        raise