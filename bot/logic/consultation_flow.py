from .data_access import save_consultation
from .validators import validate_phone, normalize_phone
from phonenumbers import NumberParseException


def request_consultation(phone: str, user_id: int = None) -> dict:
    """
    Нормализует и проверяет телефон, затем сохраняет запрос на консультацию.
    Если телефон некорректен — выбрасывает ValueError.
    """
    try:
        normalized_phone = normalize_phone(phone)
    except NumberParseException:
        raise ValueError("Неверный формат номера телефона.")

    if not validate_phone(normalized_phone):
        raise ValueError("Неверный формат номера телефона.")

    consultation_data = {
        "phone": normalized_phone,
        "user_id": user_id or 0,
        "status": "new"
    }

    save_consultation(consultation_data)
    return consultation_data
