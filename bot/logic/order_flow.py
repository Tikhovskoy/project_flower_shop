from .data_access import get_bouquets, save_order
from .validators import validate_phone, normalize_phone, normalize_datetime
from .data_access import get_compositions


def start_bouquets(min_price: int = 0, max_price: int = 9999999):
    """
    Возвращает доступные букеты в указанном диапазоне цен.
    """
    return get_bouquets(min_price, max_price)

def start_compositions(event: str, min_price: int = 0, max_price: int = 9999999):
    """
    Возвращает букеты, подходящие под указанное событие (композиции).
    Если заданы диапазоны цены, дополнительно фильтрует по цене.
    """
    bouquets = get_compositions(event)
    filtered = [b for b in bouquets if min_price <= b.price <= max_price]
    return filtered

def create_order(bouquet):
    """
    Создаёт словарь с данными о заказе на основе выбранного букета.
    """
    order_data = {
        "bouquet_id": bouquet.id,
        "bouquet_name": bouquet.name,
        "price": bouquet.price,
        "status": "new"
    }
    return order_data

def add_card_text(order_data: dict, card_text: str):
    """
    Добавляет текст открытки к заказу.
    """
    order_data["card_text"] = card_text
    return order_data

def set_contact_info(order_data: dict, customer_name: str, address: str, phone: str, delivery_time: str):
    """
    Записывает контактные данные и время доставки в заказ.
    Если номер телефона введён некорректно, выбрасывается ValueError.
    """
    try:
        normalized_phone = normalize_phone(phone)
    except Exception:
        raise ValueError("Неверный формат номера телефона.")
    
    if not validate_phone(normalized_phone):
        raise ValueError("Неверный формат номера телефона.")
    
    normalized_time = normalize_datetime(delivery_time)
    if not normalized_time:
        raise ValueError("Неверный формат времени доставки. Пример: '2025-03-27T14:00'.")
    
    order_data.update({
        "customer_name": customer_name,
        "address": address,
        "phone": normalized_phone,
        "delivery_time": normalized_time
    })
    return order_data

def confirm_order(order_data: dict) -> dict:
    """
    Подтверждает заказ и сохраняет его через data_access.save_order.
    """
    order_data["status"] = order_data.get("status", "confirmed")
    save_order(order_data)
    return order_data
