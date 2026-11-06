from unittest.mock import MagicMock

import pytest
from django.db import DatabaseError

from bot.handlers.consult_handlers import handle_consult_request, process_consult_request
from bot.models import Consultation

pytestmark = pytest.mark.django_db


def make_update(text, user_id=42, full_name="Иван Тестов"):
    update = MagicMock()
    update.message.text = text
    update.message.chat_id = 5
    update.callback_query = None
    update.effective_user.id = user_id
    update.effective_user.full_name = full_name
    return update


def test_consult_request_asks_for_phone():
    update = MagicMock()
    context = MagicMock(user_data={})

    handle_consult_request(update, context)

    assert context.user_data["awaiting_phone"] is True
    assert "номер телефона" in context.bot.send_message.call_args.kwargs["text"]


class TestProcessConsultRequest:
    def test_saves_notifies_florist_and_shows_catalog(self, settings, make_bouquet):
        settings.FLORIST_ID = 222
        make_bouquet("Облако", 990)
        update = make_update("8 (913) 123-45-67")
        context = MagicMock(user_data={"awaiting_phone": True, "order_step": "x", "order_data": 1})

        process_consult_request(update, context)

        consultation = Consultation.objects.get()
        assert (consultation.phone_number, consultation.user_id) == ("+79131234567", 42)
        assert consultation.name == "Иван Тестов"
        florist_message = context.bot.send_message.call_args_list[0].kwargs
        assert florist_message["chat_id"] == 222
        assert "+79131234567" in florist_message["text"]
        assert "Флорист скоро свяжется" in update.message.reply_text.call_args.args[0]
        assert "awaiting_phone" not in context.user_data
        assert "order_step" not in context.user_data
        assert len(context.user_data["bouquets"]) == 1

    def test_florist_is_optional(self, settings):
        settings.FLORIST_ID = None
        update = make_update("+79131234567")
        context = MagicMock(user_data={"awaiting_phone": True})

        process_consult_request(update, context)

        assert Consultation.objects.count() == 1
        context.bot.send_message.assert_not_called()

    def test_invalid_phone_asks_again(self):
        update = make_update("12345")
        context = MagicMock(user_data={"awaiting_phone": True})

        process_consult_request(update, context)

        assert "Неверный формат номера" in update.message.reply_text.call_args.args[0]
        assert context.user_data["awaiting_phone"] is True
        assert Consultation.objects.count() == 0

    def test_save_failure_is_reported_instead_of_silence(self, monkeypatch):
        def boom(data):
            raise DatabaseError("disk is full")

        monkeypatch.setattr("bot.logic.consultation_flow.save_consultation", boom)
        update = make_update("+79131234567")
        context = MagicMock(user_data={"awaiting_phone": True})

        process_consult_request(update, context)

        assert "Не удалось сохранить заявку" in update.message.reply_text.call_args.args[0]
        assert context.user_data["awaiting_phone"] is True

    def test_uses_username_when_full_name_is_empty(self):
        update = make_update("+79131234567", full_name="")
        update.effective_user.username = "ivan_t"
        context = MagicMock(user_data={})

        process_consult_request(update, context)

        assert Consultation.objects.get().name == "ivan_t"
