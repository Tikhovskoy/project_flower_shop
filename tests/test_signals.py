import pytest
from django.contrib.contenttypes.models import ContentType

from bot.models import Bouquet, OrderItem

pytestmark = pytest.mark.django_db


def add_item(order, bouquet, quantity):
    return OrderItem.objects.create(
        order=order,
        content_type=ContentType.objects.get_for_model(Bouquet),
        object_id=bouquet.pk,
        quantity=quantity,
    )


def test_order_total_follows_added_items(order, bouquet, make_bouquet):
    add_item(order, bouquet, 2)
    add_item(order, make_bouquet("Второй", 500), 1)

    order.refresh_from_db()
    assert order.order_total == bouquet.price * 2 + 500


def test_order_total_follows_deleted_items(order, bouquet):
    item = add_item(order, bouquet, 3)

    item.delete()

    order.refresh_from_db()
    assert order.order_total == 0
