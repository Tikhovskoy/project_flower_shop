import re
from datetime import datetime, timedelta

import phonenumbers
import pytz

from bot.exceptions import InvalidPhoneError

KRASNOYARSK_TZ = pytz.timezone("Asia/Krasnoyarsk")

INVALID_PHONE_MESSAGE = "Неверный формат номера. Пример: +79991234567"

# Слова вместо даты и сдвиг в днях от сегодняшнего дня
RELATIVE_DAYS = {"сегодня": 0, "завтра": 1}


def normalize_phone(phone: str) -> str:
    phone = phone.strip()
    phone = re.sub(r"[^\d+]", "", phone)
    if phone.startswith("8") and not phone.startswith("+"):
        phone = "+7" + phone[1:]

    try:
        phone_number = phonenumbers.parse(phone, "RU")
    except phonenumbers.NumberParseException as exc:
        raise InvalidPhoneError(INVALID_PHONE_MESSAGE) from exc

    if not phonenumbers.is_valid_number(phone_number):
        raise InvalidPhoneError(INVALID_PHONE_MESSAGE)

    return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)


def validate_phone(phone: str) -> bool:
    try:
        phone_number = phonenumbers.parse(phone, "RU")
    except phonenumbers.NumberParseException:
        return False
    return phonenumbers.is_valid_number(phone_number)


def _with_timezone(moment: datetime) -> datetime:
    """Время без часового пояса считаем красноярским, с поясом — оставляем как есть."""
    if moment.tzinfo is None:
        return KRASNOYARSK_TZ.localize(moment)
    return moment


def _parse_relative_day(text: str) -> datetime | None:
    """«сегодня 14:00», «завтра 09:30»."""
    for word, days in RELATIVE_DAYS.items():
        if word not in text:
            continue
        try:
            time_of_day = datetime.strptime(text.replace(word, "").strip(), "%H:%M").time()
        except ValueError:
            return None
        day = datetime.now(KRASNOYARSK_TZ) + timedelta(days=days)
        return day.replace(
            hour=time_of_day.hour, minute=time_of_day.minute, second=0, microsecond=0
        )
    return None


def normalize_datetime(dt_input) -> datetime | None:
    """Приводит ввод к datetime с часовым поясом или возвращает None, если формат не распознан.

    Понимает datetime, ISO-строки (в том числе со смещением), «dd.mm.yyyy hh:mm»,
    а также «сегодня hh:mm» и «завтра hh:mm».
    """
    if isinstance(dt_input, datetime):
        return _with_timezone(dt_input)
    if not isinstance(dt_input, str):
        return None

    text = dt_input.strip()

    try:
        return _with_timezone(datetime.fromisoformat(text))
    except ValueError:
        pass

    try:
        return _with_timezone(datetime.strptime(text, "%d.%m.%Y %H:%M"))
    except ValueError:
        pass

    return _parse_relative_day(text.lower())
