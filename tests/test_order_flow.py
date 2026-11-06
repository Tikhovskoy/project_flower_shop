from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from bot.exceptions import InvalidDateTimeError, InvalidPhoneError, OrderSaveError
from bot.logic.order_flow import (
    add_card_text,
    confirm_order,
    create_order,
    set_contact_info,
    start_bouquets,
    start_compositions,
)
from bot.models import Bouquet, Order

pytestmark = pytest.mark.django_db

NOW_IN_KRASNOYARSK = "2025-03-27T03:00:00Z"  # 10:00 по Красноярску


@pytest.fixture
def order_data(bouquet):
    return create_order(bouquet)


def fill_contacts(order_data, **overrides):
    values = {
        "customer_name": "Анна",
        "address": "ул. Тестовая, 1",
        "phone": "8 (913) 123-45-67",
        "delivery_time": "28.03.2025 14:00",
    }
    values.update(overrides)
    return set_contact_info(order_data, **values)


class TestCatalogEntryPoints:
    def test_start_bouquets_applies_price_range(self, make_bouquet):
        make_bouquet("Дешёвый", 400)
        make_bouquet("Дорогой", 3000)

        assert [b.name for b in start_bouquets(min_price=2000)] == ["Дорогой"]

    def test_start_compositions_filters_by_event(self, make_bouquet, make_composition):
        wedding = make_bouquet("Свадебный", 3000)
        make_composition("Свадьба", "wedding", [wedding])
        make_composition("ДР", "birthday", [make_bouquet("Именинный", 900)])

        assert [b.name for b in start_compositions("wedding")] == ["Свадебный"]


class TestCreateOrder:
    def test_copies_bouquet_data(self, bouquet):
        order_data = create_order(bouquet)

        assert order_data["bouquet_id"] == bouquet.id
        assert order_data["bouquet_name"] == bouquet.name
        assert order_data["price"] == bouquet.price

    def test_new_order_has_a_status_the_admin_understands(self, order_data):
        assert order_data["status"] in dict(Order.STATUS_CHOICES)


class TestAddCardText:
    def test_stores_text(self, order_data):
        result = add_card_text(order_data, "С днём рождения!")

        assert result["card_text"] == "С днём рождения!"

    def test_returns_the_same_order(self, order_data):
        assert add_card_text(order_data, "Привет") is order_data


@freeze_time(NOW_IN_KRASNOYARSK)
class TestSetContactInfo:
    def test_stores_normalized_data(self, order_data):
        result = fill_contacts(order_data)

        assert result["customer_name"] == "Анна"
        assert result["delivery_address"] == "ул. Тестовая, 1"
        assert result["phone_number"] == "+79131234567"
        assert result["delivery_time"].utcoffset() == timedelta(hours=7)
        assert (result["delivery_time"].day, result["delivery_time"].hour) == (28, 14)

    def test_accepts_datetime_as_delivery_time(self, order_data):
        result = fill_contacts(order_data, delivery_time=datetime(2025, 3, 28, 9, 0))

        assert result["delivery_time"].hour == 9

    def test_invalid_phone_raises_and_changes_nothing(self, order_data):
        with pytest.raises(InvalidPhoneError):
            fill_contacts(order_data, phone="12345")

        assert "phone_number" not in order_data
        assert "customer_name" not in order_data

    def test_invalid_time_raises_and_changes_nothing(self, order_data):
        with pytest.raises(InvalidDateTimeError):
            fill_contacts(order_data, delivery_time="когда-нибудь")

        assert "delivery_time" not in order_data
        assert "customer_name" not in order_data

    def test_phone_is_checked_before_time(self, order_data):
        with pytest.raises(InvalidPhoneError):
            fill_contacts(order_data, phone="abc", delivery_time="тоже мусор")

    def test_validation_errors_are_logged(self, order_data, caplog):
        with pytest.raises(InvalidPhoneError), caplog.at_level("WARNING", logger="bot_logger"):
            fill_contacts(order_data, phone="12345")

        assert "Валидация" in caplog.text


@freeze_time(NOW_IN_KRASNOYARSK)
class TestConfirmOrder:
    @pytest.fixture
    def ready_order(self, order_data):
        add_card_text(order_data, "С днём рождения!")
        return fill_contacts(order_data)

    def test_saves_order_to_database(self, ready_order, bouquet):
        result = confirm_order(ready_order)

        order = Order.objects.get()
        assert result is ready_order
        assert order.customer_name == "Анна"
        assert order.phone_number == "+79131234567"
        assert order.postcard == "С днём рождения!"
        assert order.order_total == bouquet.price
        assert order.items.get().product == bouquet

    def test_saved_status_is_valid(self, ready_order):
        confirm_order(ready_order)

        assert Order.objects.get().status in dict(Order.STATUS_CHOICES)

    def test_failure_is_reported_as_order_save_error(self, ready_order, bouquet):
        Bouquet.objects.filter(pk=bouquet.pk).delete()

        with pytest.raises(OrderSaveError):
            confirm_order(ready_order)

        assert Order.objects.count() == 0

    def test_original_cause_is_preserved(self, ready_order, bouquet):
        Bouquet.objects.filter(pk=bouquet.pk).delete()

        with pytest.raises(OrderSaveError) as error:
            confirm_order(ready_order)

        assert isinstance(error.value.__cause__, Bouquet.DoesNotExist)
