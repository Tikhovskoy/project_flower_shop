from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from bot.exceptions import OrderSaveError
from bot.logging_tools import log_unexpected_error

from .data_access import get_bouquets, get_compositions, save_order
from .order_draft import OrderDraft


def start_bouquets(min_price: int | None = 0, max_price: int | None = None):
    return get_bouquets(min_price, max_price)


def start_compositions(event: str, min_price: int | None = 0, max_price: int | None = None):
    return get_compositions(event, min_price, max_price)


def create_order(bouquet) -> OrderDraft:
    return OrderDraft.from_bouquet(bouquet)


def confirm_order(order: OrderDraft) -> OrderDraft:
    try:
        save_order(order)
    except (DatabaseError, ObjectDoesNotExist) as e:
        log_unexpected_error("Ошибка в confirm_order при сохранении заказа", e)
        raise OrderSaveError("Не удалось сохранить заказ.") from e
    return order
