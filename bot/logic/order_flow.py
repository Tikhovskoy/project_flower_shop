from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from bot.exceptions import InvalidDateTimeError, InvalidPhoneError, OrderSaveError
from bot.logging_tools import log_unexpected_error, log_validation_error

from .data_access import get_bouquets, get_compositions, save_order
from .validators import normalize_datetime, normalize_phone


def start_bouquets(min_price: int | None = 0, max_price: int | None = None):
    return get_bouquets(min_price, max_price)


def start_compositions(event: str, min_price: int | None = 0, max_price: int | None = None):
    return get_compositions(event, min_price, max_price)


def create_order(bouquet):
    return {
        "bouquet_id": bouquet.id,
        "bouquet_name": bouquet.name,
        "price": bouquet.price,
        "status": "accepted",
    }


def add_card_text(order_data: dict, card_text: str):
    order_data["card_text"] = card_text
    return order_data


def set_contact_info(order_data: dict, customer_name: str, address: str, phone: str, delivery_time: str):
    try:
        normalized_phone = normalize_phone(phone)
    except InvalidPhoneError as e:
        log_validation_error("Ошибка normalize_phone", e)
        raise

    normalized_time = normalize_datetime(delivery_time)
    if not normalized_time:
        log_validation_error("normalize_datetime вернул None", ValueError(f"Невалидная дата: {delivery_time!r}"))
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
        save_order(order_data)
    except (DatabaseError, ObjectDoesNotExist) as e:
        log_unexpected_error("Ошибка в confirm_order при сохранении заказа", e)
        raise OrderSaveError("Не удалось сохранить заказ.") from e
    return order_data
