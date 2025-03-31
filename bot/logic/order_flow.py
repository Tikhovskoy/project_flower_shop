from .data_access import get_bouquets, save_order, get_compositions
from .validators import validate_phone, normalize_phone, normalize_datetime
from bot.logging_tools import log_validation_error, log_unexpected_error
from bot.exceptions import InvalidPhoneError, InvalidDateTimeError, OrderSaveError 


def start_bouquets(min_price: int = 0, max_price: int = 9999999):
    return get_bouquets(min_price, max_price)


def start_compositions(event: str, min_price: int = 0, max_price: int = 9999999):
    return get_compositions(event, min_price, max_price)


def create_order(bouquet):
    return {
        "bouquet_id": bouquet.id,
        "bouquet_name": bouquet.name,
        "price": bouquet.price,
        "status": "new"
    }


def add_card_text(order_data: dict, card_text: str):
    order_data["card_text"] = card_text
    return order_data


def set_contact_info(order_data: dict, customer_name: str, address: str, phone: str, delivery_time: str):
    try:
        normalized_phone = normalize_phone(phone)
    except Exception as e:
        log_validation_error("Ошибка normalize_phone", e)
        raise InvalidPhoneError("Неверный формат номера телефона.")

    if not validate_phone(normalized_phone):
        log_validation_error("validate_phone вернул False", Exception("Невалидный номер"))
        raise InvalidPhoneError("Неверный формат номера телефона.")

    normalized_time = normalize_datetime(delivery_time)
    if not normalized_time:
        log_validation_error("normalize_datetime вернул None", Exception("Невалидная дата"))
        raise InvalidDateTimeError("Неверный формат времени доставки. Пример: '2025-03-27T14:00'.")

    order_data.update({
        "customer_name": customer_name,
        "delivery_address": address,
        "phone_number": normalized_phone,
        "delivery_time": normalized_time
    })
    return order_data

def confirm_order(order_data: dict) -> dict:
    try:
        order_data["status"] = order_data.get("status", "confirmed")
        save_order(order_data)
        return order_data
    except Exception as e:
        log_unexpected_error("Ошибка в confirm_order при сохранении заказа", e)
        raise OrderSaveError("Не удалось сохранить заказ.")
