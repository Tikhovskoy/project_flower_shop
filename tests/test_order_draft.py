from datetime import datetime, timedelta

import pytest
import pytz
from freezegun import freeze_time

from bot.exceptions import InvalidDateTimeError, InvalidPhoneError
from bot.logic.order_draft import OrderDraft
from bot.models import Order

KRASNOYARSK = pytz.timezone("Asia/Krasnoyarsk")
NOW_IN_KRASNOYARSK = "2025-03-27T03:00:00Z"  # 10:00 по Красноярску


@pytest.fixture
def draft(bouquet):
    return OrderDraft.from_bouquet(bouquet)


def fill_contacts(draft, **overrides):
    values = {
        "customer_name": "Анна",
        "address": "ул. Тестовая, 1",
        "phone": "8 (913) 123-45-67",
        "delivery_time": "28.03.2025 14:00",
    }
    values.update(overrides)
    return draft.set_contact_info(**values)


class TestCreation:
    def test_from_bouquet_copies_bouquet_data(self, bouquet):
        draft = OrderDraft.from_bouquet(bouquet)

        assert draft.bouquet_id == bouquet.id
        assert draft.bouquet_name == bouquet.name
        assert draft.price == bouquet.price

    def test_new_draft_is_empty_and_has_a_valid_status(self, draft):
        assert draft.status in dict(Order.STATUS_CHOICES)
        assert draft.card_text == draft.customer_name == draft.phone_number == ""
        assert draft.delivery_time is None


class TestAddCardText:
    def test_stores_text(self, draft):
        draft.add_card_text("С днём рождения!")

        assert draft.card_text == "С днём рождения!"

    def test_returns_self_for_chaining(self, draft):
        assert draft.add_card_text("Привет") is draft


@freeze_time(NOW_IN_KRASNOYARSK)
class TestSetContactInfo:
    def test_stores_normalized_data(self, draft):
        result = fill_contacts(draft)

        assert result is draft
        assert draft.customer_name == "Анна"
        assert draft.delivery_address == "ул. Тестовая, 1"
        assert draft.phone_number == "+79131234567"
        assert draft.delivery_time == KRASNOYARSK.localize(datetime(2025, 3, 28, 14, 0))

    def test_accepts_datetime_as_delivery_time(self, draft):
        fill_contacts(draft, delivery_time=datetime(2025, 3, 28, 9, 0))

        assert draft.delivery_time.hour == 9
        assert draft.delivery_time.utcoffset() == timedelta(hours=7)

    def test_accepts_relative_day(self, draft):
        fill_contacts(draft, delivery_time="завтра 09:30")

        assert (draft.delivery_time.day, draft.delivery_time.hour) == (28, 9)

    def test_invalid_phone_raises_and_changes_nothing(self, draft):
        before = OrderDraft(**vars(draft))

        with pytest.raises(InvalidPhoneError):
            fill_contacts(draft, phone="12345")

        assert draft == before

    def test_invalid_time_raises_and_changes_nothing(self, draft):
        before = OrderDraft(**vars(draft))

        with pytest.raises(InvalidDateTimeError):
            fill_contacts(draft, delivery_time="когда-нибудь")

        assert draft == before

    def test_phone_is_checked_before_time(self, draft):
        with pytest.raises(InvalidPhoneError):
            fill_contacts(draft, phone="abc", delivery_time="тоже мусор")

    def test_validation_errors_are_logged(self, draft, caplog):
        with pytest.raises(InvalidDateTimeError), caplog.at_level("WARNING", logger="bot_logger"):
            fill_contacts(draft, delivery_time="когда-нибудь")

        assert "Валидация" in caplog.text


@freeze_time(NOW_IN_KRASNOYARSK)
class TestCourierMessage:
    def test_contains_every_detail(self, draft):
        fill_contacts(draft)

        message = draft.courier_message()

        assert "Новый заказ" in message
        assert f"Букет: {draft.bouquet_name}" in message
        assert f"Цена: {draft.price}₽" in message
        assert "Получатель: Анна" in message
        assert "Адрес: ул. Тестовая, 1" in message
        assert "Время доставки: 28.03 14:00" in message
        assert "Телефон: +79131234567" in message

    def test_card_is_included_only_when_present(self, draft):
        fill_contacts(draft)
        assert "Открытка" not in draft.courier_message()

        draft.add_card_text("С днём рождения!")

        assert "💌 Открытка: С днём рождения!" in draft.courier_message()
