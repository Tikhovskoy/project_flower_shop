from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from bot.models import Bouquet, Consultation, Order, OrderItem

from .order_draft import OrderDraft


def _in_price_range(bouquets, min_price, max_price):
    """Ограничивает выборку по цене; None вместо границы означает «без ограничения»."""
    if min_price is not None:
        bouquets = bouquets.filter(price__gte=min_price)
    if max_price is not None:
        bouquets = bouquets.filter(price__lte=max_price)
    return bouquets


def get_bouquets(min_price=0, max_price=None):
    available = Bouquet.objects.filter(is_available=True)
    return list(_in_price_range(available, min_price, max_price).order_by("id"))


def get_compositions(event=None, min_price=0, max_price=None):
    """Букеты из доступных композиций события; без события — весь каталог."""
    bouquets = Bouquet.objects.filter(is_available=True)
    if event:
        bouquets = bouquets.filter(
            compositions__event=event,
            compositions__is_available=True,
        ).distinct()
    return list(_in_price_range(bouquets, min_price, max_price).order_by("id"))


def save_order(draft: OrderDraft) -> Order:
    """Сохраняет заказ вместе с позицией. Всё или ничего: частично заказ не записывается."""
    with transaction.atomic():
        bouquet = Bouquet.objects.get(id=draft.bouquet_id)
        order = Order.objects.create(
            customer_name=draft.customer_name,
            phone_number=draft.phone_number,
            delivery_address=draft.delivery_address,
            postcard=draft.card_text,
            delivery_time=draft.delivery_time,
            status=draft.status,
        )
        OrderItem.objects.create(
            order=order,
            content_type=ContentType.objects.get_for_model(bouquet),
            object_id=bouquet.id,
            quantity=1,
        )
        order.calculate_total()
    return order


def save_consultation(consultation_data: dict) -> Consultation:
    return Consultation.objects.create(
        user_id=consultation_data.get("user_id", 0),
        phone_number=consultation_data["phone"],
        status=consultation_data.get("status", "new"),
        name=consultation_data.get("name", "(аноним)"),
    )
