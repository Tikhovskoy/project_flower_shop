from datetime import datetime, timedelta
import phonenumbers
import pytz
import re

KRASNOYARSK_TZ = pytz.timezone('Asia/Krasnoyarsk')

def normalize_phone(phone: str) -> str:
    phone = phone.strip()
    phone = re.sub(r"[^\d+]", "", phone)
    if phone.startswith("8") and not phone.startswith("+"):
        phone = "+7" + phone[1:]
    phone_number = phonenumbers.parse(phone, "RU")
    formatted = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
    print(f"[DEBUG] normalize_phone: {phone} -> {formatted}")
    return formatted

def validate_phone(phone: str) -> bool:
    try:
        phone_number = phonenumbers.parse(phone, "RU")
        return phonenumbers.is_valid_number(phone_number)
    except phonenumbers.NumberParseException:
        return False

def normalize_datetime(datetime_str: str) -> datetime:
    print(f"[DEBUG] Введено время доставки: {datetime_str}")
    datetime_str = datetime_str.strip().lower()

    try:
        dt = datetime.fromisoformat(datetime_str)
        print(f"[DEBUG] Парсинг ISO: {dt}")
        return KRASNOYARSK_TZ.localize(dt)
    except ValueError:
        pass

    try:
        dt = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
        dt = KRASNOYARSK_TZ.localize(dt)
        print(f"[DEBUG] Парсинг даты с точкой: {dt}")
        return dt
    except ValueError:
        pass

    if "сегодня" in datetime_str:
        try:
            time_part = datetime_str.replace("сегодня", "").strip()
            time_obj = datetime.strptime(time_part, "%H:%M").time()
            now = datetime.now(KRASNOYARSK_TZ)
            dt = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            print(f"[DEBUG] Парсинг 'сегодня': {dt}")
            return dt
        except ValueError:
            pass

    if "завтра" in datetime_str:
        try:
            time_part = datetime_str.replace("завтра", "").strip()
            time_obj = datetime.strptime(time_part, "%H:%M").time()
            now = datetime.now(KRASNOYARSK_TZ) + timedelta(days=1)
            dt = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            print(f"[DEBUG] Парсинг 'завтра': {dt}")
            return dt
        except ValueError:
            pass

    print("[DEBUG] Неверный формат времени доставки.")
    return None