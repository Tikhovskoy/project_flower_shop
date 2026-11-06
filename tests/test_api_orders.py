import pytest
from django.contrib.contenttypes.models import ContentType

from bot.models import Bouquet, Order

pytestmark = pytest.mark.django_db


def test_admin_creates_order_with_items(admin_client_api, bouquet):
    payload = {
        "customer_name": "Анна",
        "phone_number": "+79990001122",
        "delivery_address": "ул. Тестовая, 1",
        "items": [
            {
                "content_type": ContentType.objects.get_for_model(Bouquet).pk,
                "object_id": bouquet.pk,
                "quantity": 2,
            }
        ],
    }

    response = admin_client_api.post("/api/order/create/", payload, format="json")

    assert response.status_code == 201
    order = Order.objects.get()
    assert order.items.get().quantity == 2
    assert order.order_total == bouquet.price * 2
    assert len(response.json()["items"]) == 1


def test_order_without_required_fields_is_rejected(admin_client_api):
    response = admin_client_api.post("/api/order/create/", {"customer_name": "Анна"}, format="json")

    assert response.status_code == 400
    assert Order.objects.count() == 0
