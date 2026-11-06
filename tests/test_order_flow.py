import pytest
from freezegun import freeze_time

from bot.exceptions import OrderSaveError
from bot.logic.order_draft import OrderDraft
from bot.logic.order_flow import (
    confirm_order,
    create_order,
    start_bouquets,
    start_compositions,
)
from bot.models import Bouquet, Order

pytestmark = pytest.mark.django_db

NOW_IN_KRASNOYARSK = "2025-03-27T03:00:00Z"  # 10:00 по Красноярску


class TestCatalogEntryPoints:
    def test_start_bouquets_applies_price_range(self, make_bouquet):
        make_bouquet("Дешёвый", 400)
        make_bouquet("Дорогой", 3000)

        assert [b.name for b in start_bouquets(min_price=2000)] == ["Дорогой"]

    def test_start_bouquets_has_no_upper_bound_by_default(self, make_bouquet):
        make_bouquet("Эксклюзив", 15_000_000)

        assert [b.name for b in start_bouquets()] == ["Эксклюзив"]

    def test_start_compositions_filters_by_event(self, make_bouquet, make_composition):
        wedding = make_bouquet("Свадебный", 3000)
        make_composition("Свадьба", "wedding", [wedding])
        make_composition("ДР", "birthday", [make_bouquet("Именинный", 900)])

        assert [b.name for b in start_compositions("wedding")] == ["Свадебный"]


def test_create_order_returns_draft_for_the_bouquet(bouquet):
    draft = create_order(bouquet)

    assert isinstance(draft, OrderDraft)
    assert draft.bouquet_id == bouquet.id


@freeze_time(NOW_IN_KRASNOYARSK)
class TestConfirmOrder:
    @pytest.fixture
    def ready_order(self, bouquet):
        draft = create_order(bouquet).add_card_text("С днём рождения!")
        return draft.set_contact_info("Анна", "ул. Тестовая, 1", "8 (913) 123-45-67", "28.03.2025 14:00")

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

    def test_failure_is_logged(self, ready_order, bouquet, caplog):
        Bouquet.objects.filter(pk=bouquet.pk).delete()

        with pytest.raises(OrderSaveError), caplog.at_level("ERROR", logger="bot_logger"):
            confirm_order(ready_order)

        assert "confirm_order" in caplog.text
