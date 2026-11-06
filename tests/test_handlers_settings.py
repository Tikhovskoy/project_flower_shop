from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from bot.handlers.order_handlers import send_order_to_courier
from bot.logic.order_draft import OrderDraft

BOT_DIR = Path(__file__).resolve().parent.parent / "bot"


@pytest.fixture
def order():
    return OrderDraft(
        bouquet_id=1,
        bouquet_name="Облако",
        price=990,
        customer_name="Анна",
        delivery_address="ул. Тестовая, 1",
        delivery_time=datetime(2025, 3, 27, 14, 0),
        phone_number="+79990001122",
    )


def test_courier_id_is_taken_from_django_settings(settings, order):
    settings.COURIER_ID = 111
    context = MagicMock()

    send_order_to_courier(context, order)

    context.bot.send_message.assert_called_once_with(chat_id=111, text=order.courier_message())


def test_nothing_is_sent_when_courier_id_is_not_configured(settings, order):
    settings.COURIER_ID = None
    context = MagicMock()

    send_order_to_courier(context, order)

    context.bot.send_message.assert_not_called()


@pytest.mark.parametrize("package", ["handlers", "logic"])
def test_handlers_and_logic_do_not_read_environment_directly(package):
    """Все настройки идут через django.conf.settings, а не через os.getenv."""
    offenders = []
    for path in (BOT_DIR / package).rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if "os.getenv" in source or "os.environ" in source:
            offenders.append(str(path.relative_to(BOT_DIR)))

    assert offenders == [], offenders
