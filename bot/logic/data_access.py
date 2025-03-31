from bot.models import Bouquet, Composition, Order, OrderItem, Consultation
from django.utils.timezone import make_aware
from django.contrib.contenttypes.models import ContentType
from datetime import datetime
import pytz
from bot.logging_tools import log_unexpected_error


def get_bouquets(min_price=0, max_price=9999999):
    return list(Bouquet.objects.filter(
        is_available=True,
        price__gte=min_price,
        price__lte=max_price
    ))


def get_compositions(event=None, min_price=0, max_price=9999999):
    if not event:
        return list(Bouquet.objects.filter(
            is_available=True,
            price__gte=min_price,
            price__lte=max_price
        ))

    matching_bouquets = set()
    compositions = Composition.objects.filter(event=event)
    for composition in compositions:
        for bouquet in composition.bouquets.filter(
            is_available=True,
            price__gte=min_price,
            price__lte=max_price
        ):
            matching_bouquets.add(bouquet)

    return list(matching_bouquets)


def save_order(order_data: dict):
    try:
        delivery_time = order_data.get("delivery_time")
        if delivery_time and isinstance(delivery_time, str):
            delivery_time = datetime.fromisoformat(delivery_time)
        if delivery_time and delivery_time.tzinfo is None:
            delivery_time = make_aware(delivery_time, pytz.timezone("Asia/Krasnoyarsk"))

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
