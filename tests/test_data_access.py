from datetime import datetime

import pytest
import pytz
from django.db import DatabaseError

from bot.logic.data_access import get_bouquets, get_compositions, save_consultation, save_order
from bot.models import Bouquet, Consultation, Order

pytestmark = pytest.mark.django_db

KRASNOYARSK = pytz.timezone("Asia/Krasnoyarsk")


def names(bouquets):
    return sorted(bouquet.name for bouquet in bouquets)


@pytest.fixture
def catalog(make_bouquet):
    return {
        "cheap": make_bouquet("Дешёвый", 450),
        "mid": make_bouquet("Средний", 1000),
        "upper": make_bouquet("Дорогой", 1500),
        "pricey": make_bouquet("Королевский", 2500),
        "hidden": make_bouquet("Снят с продажи", 700, is_available=False),
    }


class TestGetBouquets:
    def test_returns_all_available_by_default(self, catalog):
        assert names(get_bouquets()) == ["Дешёвый", "Дорогой", "Королевский", "Средний"]

    def test_never_returns_unavailable_bouquets(self, catalog):
        assert "Снят с продажи" not in names(get_bouquets(0, 10_000))

    def test_price_bounds_are_inclusive(self, catalog):
        assert names(get_bouquets(min_price=450, max_price=1000)) == ["Дешёвый", "Средний"]

    def test_only_min_price(self, catalog):
        assert names(get_bouquets(min_price=2000)) == ["Королевский"]

    def test_only_max_price(self, catalog):
        assert names(get_bouquets(max_price=500)) == ["Дешёвый"]

    def test_empty_range_gives_empty_list(self, catalog):
        assert get_bouquets(min_price=5000, max_price=6000) == []

    def test_returns_list(self, catalog):
        assert isinstance(get_bouquets(), list)


class TestGetCompositions:
    @pytest.fixture
    def compositions(self, catalog, make_composition):
        birthday = make_composition(
            "День рождения", "birthday", [catalog["cheap"], catalog["mid"], catalog["hidden"]]
        )
        birthday_two = make_composition("Именинница", "birthday", [catalog["mid"], catalog["upper"]])
        wedding = make_composition("Свадьба", "wedding", [catalog["pricey"]])
        return birthday, birthday_two, wedding

    def test_collects_bouquets_of_the_event(self, compositions):
        assert names(get_compositions("birthday")) == ["Дешёвый", "Дорогой", "Средний"]

    def test_bouquet_from_two_compositions_is_returned_once(self, compositions):
        assert names(get_compositions("birthday")).count("Средний") == 1

    def test_other_events_are_excluded(self, compositions):
        assert names(get_compositions("wedding")) == ["Королевский"]

    def test_unavailable_bouquets_are_excluded(self, compositions):
        assert "Снят с продажи" not in names(get_compositions("birthday"))

    def test_price_range_applies_inside_event(self, compositions):
        assert names(get_compositions("birthday", 500, 1200)) == ["Средний"]

    def test_unknown_event_gives_empty_list(self, compositions):
        assert get_compositions("school") == []

    def test_without_event_falls_back_to_whole_catalog(self, compositions):
        assert names(get_compositions(None, 0, 1000)) == ["Дешёвый", "Средний"]

    def test_composition_taken_off_sale_is_not_shown(self, catalog, make_composition):
        make_composition("Снята", "school", [catalog["cheap"]], is_available=False)

        assert get_compositions("school") == []

    def test_bouquet_stays_visible_through_another_available_composition(
        self, catalog, make_composition
    ):
        make_composition("Снята", "school", [catalog["cheap"]], is_available=False)
        make_composition("Работает", "school", [catalog["cheap"]])

        assert names(get_compositions("school")) == ["Дешёвый"]


class TestSaveOrder:
    @pytest.fixture
    def order_data(self, catalog):
        return {
            "bouquet_id": catalog["mid"].id,
            "bouquet_name": "Средний",
            "price": 1000,
            "customer_name": "Анна",
            "delivery_address": "ул. Тестовая, 1",
            "phone_number": "+79131234567",
            "delivery_time": KRASNOYARSK.localize(datetime(2025, 3, 28, 14, 0)),
            "card_text": "С днём рождения!",
            "status": "accepted",
        }

    def test_creates_order_with_item_and_total(self, order_data, catalog):
        save_order(order_data)

        order = Order.objects.get()
        assert (order.customer_name, order.phone_number) == ("Анна", "+79131234567")
        assert order.delivery_address == "ул. Тестовая, 1"
        assert order.postcard == "С днём рождения!"
        assert order.order_total == 1000
        item = order.items.get()
        assert (item.product, item.quantity) == (catalog["mid"], 1)

    def test_naive_delivery_time_becomes_aware(self, order_data):
        order_data["delivery_time"] = datetime(2025, 3, 28, 14, 0)

        save_order(order_data)

        assert Order.objects.get().delivery_time == KRASNOYARSK.localize(datetime(2025, 3, 28, 14, 0))

    def test_iso_string_delivery_time_is_accepted(self, order_data):
        order_data["delivery_time"] = "2025-03-28T14:00"

        save_order(order_data)

        assert Order.objects.get().delivery_time == KRASNOYARSK.localize(datetime(2025, 3, 28, 14, 0))


class TestSaveConsultation:
    def test_saves_all_fields(self):
        save_consultation(
            {"phone": "+79131234567", "user_id": 42, "name": "Иван", "status": "in_progress"}
        )

        consultation = Consultation.objects.get()
        assert (consultation.phone_number, consultation.user_id) == ("+79131234567", 42)
        assert (consultation.name, consultation.status) == ("Иван", "in_progress")

    def test_uses_defaults_for_optional_fields(self):
        save_consultation({"phone": "+79131234567"})

        consultation = Consultation.objects.get()
        assert consultation.name == "(аноним)"
        assert consultation.status == "new"

    def test_database_errors_are_not_swallowed(self, monkeypatch):
        def boom(**kwargs):
            raise DatabaseError("disk is full")

        monkeypatch.setattr(Consultation.objects, "create", boom)

        with pytest.raises(DatabaseError):
            save_consultation({"phone": "+79131234567"})
