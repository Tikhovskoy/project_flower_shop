from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from bot.handlers.order_handlers import (
    handle_card_choice,
    handle_order_start,
    process_order_step,
)
from bot.logic.order_draft import OrderDraft
from bot.models import Bouquet, Order

pytestmark = pytest.mark.django_db

NOW_IN_KRASNOYARSK = "2025-03-27T03:00:00Z"  # 10:00 по Красноярску


def message(text):
    update = MagicMock()
    update.message.text = text
    return update


def replies(update):
    return [call.args[0] for call in update.message.reply_text.call_args_list]


@pytest.fixture
def context(bouquet):
    context = MagicMock()
    context.user_data = {
        "order_step": "card_text",
        "order_data": OrderDraft.from_bouquet(bouquet),
    }
    return context


def send(context, text):
    update = message(text)
    process_order_step(update, context)
    return update


def test_order_start_creates_draft_for_current_bouquet(bouquet):
    context = MagicMock(user_data={"bouquets": [bouquet], "current_bouquet": 0})
    update = MagicMock()

    handle_order_start(update, context)

    assert isinstance(context.user_data["order_data"], OrderDraft)
    assert context.user_data["order_data"].bouquet_id == bouquet.id
    assert context.user_data["order_step"] == "card"


@pytest.mark.parametrize(
    ("choice", "next_step"), [("add_card_yes", "card_text"), ("add_card_no", "name")]
)
def test_card_choice_selects_next_step(choice, next_step):
    update = MagicMock()
    update.callback_query.data = choice
    context = MagicMock(user_data={})

    handle_card_choice(update, context)

    assert context.user_data["order_step"] == next_step


@freeze_time(NOW_IN_KRASNOYARSK)
class TestOrderDialog:
    def test_full_happy_path_saves_order_and_notifies_courier(self, settings, context, bouquet):
        settings.COURIER_ID = 111

        send(context, "С днём рождения!")
        send(context, "Анна")
        send(context, "ул. Тестовая, 1")
        send(context, "28.03.2025 14:00")
        final = send(context, "8 (913) 123-45-67")

        order = Order.objects.get()
        assert order.postcard == "С днём рождения!"
        assert order.customer_name == "Анна"
        assert order.phone_number == "+79131234567"
        assert order.items.get().product == bouquet
        assert "Заказ подтверждён" in replies(final)[-1]
        courier_call = context.bot.send_message.call_args
        assert courier_call.kwargs["chat_id"] == 111
        assert "Анна" in courier_call.kwargs["text"]
        assert context.user_data == {}

    def test_steps_follow_one_another(self, context):
        context.user_data["order_step"] = "name"

        send(context, "Анна")
        assert context.user_data["order_step"] == "address"

        send(context, "ул. Тестовая, 1")
        assert context.user_data["order_step"] == "delivery_time"

        send(context, "завтра 12:00")
        assert context.user_data["order_step"] == "phone"

    def test_bad_delivery_time_asks_again_and_stays_on_step(self, context):
        context.user_data["order_step"] = "delivery_time"

        update = send(context, "когда-нибудь")

        assert context.user_data["order_step"] == "delivery_time"
        assert "Неверный формат даты" in replies(update)[0]
        assert "delivery_time" not in context.user_data

    def test_bad_phone_asks_again_and_saves_nothing(self, context):
        context.user_data.update(
            order_step="phone",
            customer_name="Анна",
            address="ул. Тестовая, 1",
            delivery_time="28.03.2025 14:00",
        )

        update = send(context, "12345")

        assert context.user_data["order_step"] == "phone"
        assert "Пожалуйста, повторите ввод" in replies(update)[0]
        assert Order.objects.count() == 0

    def test_save_failure_is_reported_to_user(self, context, bouquet):
        context.user_data.update(
            order_step="phone",
            customer_name="Анна",
            address="ул. Тестовая, 1",
            delivery_time="28.03.2025 14:00",
        )
        Bouquet.objects.filter(pk=bouquet.pk).delete()

        update = send(context, "8 (913) 123-45-67")

        assert "Не удалось сохранить заказ" in replies(update)[0]
        assert Order.objects.count() == 0

    def test_unknown_step_resets_dialog(self, context):
        context.user_data["order_step"] = "что-то странное"

        update = send(context, "привет")

        assert "Неожиданный шаг" in replies(update)[0]
        assert context.user_data == {}
