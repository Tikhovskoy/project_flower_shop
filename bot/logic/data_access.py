from bot.models import Bouquet, Composition, Order, OrderItem, Consultation
from django.db import transaction
from django.utils.timezone import make_aware
from django.contrib.contenttypes.models import ContentType
from datetime import datetime
import pytz
from bot.logging_tools import log_unexpected_error


def _in_price_range(bouquets, min_price, max_price):
    """Ограничивает выборку по цене; None вместо границы означает «без ограничения»."""
    if min_price is not None:
        bouquets = bouquets.filter(price__gte=min_price)
    if max_price is not None:
        bouquets = bouquets.filter(price__lte=max_price)
    return bouquets


def get_bouquets(min_price=0, max_price=None):
    available = Bouquet.objects.filter(is_available=True)
    return list(_in_price_range(available, min_price, max_price).order_by('id'))


def get_compositions(event=None, min_price=0, max_price=None):
    """Букеты из доступных композиций события; без события — весь каталог."""
    bouquets = Bouquet.objects.filter(is_available=True)
    if event:
        bouquets = bouquets.filter(
            compositions__event=event,
            compositions__is_available=True,
        ).distinct()
    return list(_in_price_range(bouquets, min_price, max_price).order_by('id'))


def save_order(order_data: dict):
    try:
        delivery_time = order_data.get("delivery_time")
        if delivery_time and isinstance(delivery_time, str):
            delivery_time = datetime.fromisoformat(delivery_time)
        if delivery_time and delivery_time.tzinfo is None:
            delivery_time = make_aware(delivery_time, pytz.timezone("Asia/Krasnoyarsk"))

        with transaction.atomic():
            order = Order.objects.create(
                customer_name=order_data.get("customer_name", ""),
                phone_number=order_data.get("phone_number", ""),
                delivery_address=order_data.get("delivery_address", ""),
                postcard=order_data.get("card_text", ""),
                delivery_time=delivery_time,
                status=order_data.get("status", "new"),
            )

            bouquet = Bouquet.objects.get(id=order_data["bouquet_id"])
            content_type = ContentType.objects.get_for_model(bouquet)

            OrderItem.objects.create(
                order=order,
                content_type=content_type,
                object_id=bouquet.id,
                quantity=1
            )

            order.calculate_total()

    except Exception as e:
        log_unexpected_error("Ошибка при сохранении заказа в save_order", e)
        raise


def save_consultation(consultation_data: dict):
    try:
        Consultation.objects.create(
            user_id=consultation_data.get("user_id", 0),
            phone_number=consultation_data["phone"],
            status=consultation_data.get("status", "new"),
            name=consultation_data.get("name", "(аноним)")
        )
    except Exception as e:
        log_unexpected_error("Ошибка при сохранении консультации в save_consultation", e)
        raise
