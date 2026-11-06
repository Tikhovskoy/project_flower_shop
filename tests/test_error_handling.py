import logging
from unittest.mock import MagicMock

import pytest
from django.db import DatabaseError
from telegram.error import BadRequest, NetworkError, TelegramError

from bot.exceptions import ConsultationSaveError
from bot.handlers.errors import handle_error
from bot.handlers.start_handlers import DEFAULT_REPLY, handle_messages
from bot.logic import consultation_flow
from bot.logic.consultation_flow import request_consultation
from bot.message_tools import safe_delete_message
from bot.models import Consultation


class TestConsultationSaveErrors:
    @pytest.fixture
    def broken_database(self, monkeypatch):
        def boom(data):
            raise DatabaseError("disk is full")

        monkeypatch.setattr(consultation_flow, "save_consultation", boom)

    def test_database_error_becomes_consultation_save_error(self, broken_database):
        with pytest.raises(ConsultationSaveError) as error:
            request_consultation("+79131234567", user_id=1)

        assert isinstance(error.value.__cause__, DatabaseError)

    def test_database_error_is_logged(self, broken_database, caplog):
        with pytest.raises(ConsultationSaveError), caplog.at_level(logging.ERROR, logger="bot_logger"):
            request_consultation("+79131234567", user_id=1)

        assert "request_consultation" in caplog.text

    @pytest.mark.django_db
    def test_programming_errors_are_not_disguised(self, monkeypatch):
        def broken(data):
            raise KeyError("phone")

        monkeypatch.setattr(consultation_flow, "save_consultation", broken)

        with pytest.raises(KeyError):
            request_consultation("+79131234567", user_id=1)

        assert Consultation.objects.count() == 0


class TestSafeDeleteMessage:
    @pytest.mark.parametrize("error", [BadRequest("gone"), NetworkError("down"), TelegramError("?")])
    def test_telegram_errors_are_ignored(self, error):
        query = MagicMock()
        query.message.delete.side_effect = error

        safe_delete_message(query)

    def test_message_is_deleted(self):
        query = MagicMock()

        safe_delete_message(query)

        query.message.delete.assert_called_once_with()

    def test_nothing_to_delete(self):
        query = MagicMock(message=None)

        safe_delete_message(query)

    def test_unexpected_errors_are_not_swallowed(self):
        query = MagicMock()
        query.message.delete.side_effect = RuntimeError("bug")

        with pytest.raises(RuntimeError):
            safe_delete_message(query)


class TestGlobalErrorHandler:
    def test_logs_error_with_traceback_and_apologises(self, caplog):
        update = MagicMock()
        context = MagicMock()
        try:
            raise ValueError("boom")
        except ValueError as error:
            context.error = error

        with caplog.at_level(logging.ERROR, logger="bot_logger"):
            handle_error(update, context)

        assert "boom" in caplog.text
        assert "Traceback" in caplog.text
        update.effective_message.reply_text.assert_called_once()

    def test_works_when_update_is_not_a_message(self, caplog):
        context = MagicMock(error=RuntimeError("polling failed"))

        with caplog.at_level(logging.ERROR, logger="bot_logger"):
            handle_error(None, context)

        assert "polling failed" in caplog.text


class TestHandleMessages:
    @staticmethod
    def update(text="привет"):
        update = MagicMock()
        update.message.text = text
        return update

    def test_unknown_text_gets_default_reply(self):
        update = self.update()

        handle_messages(update, MagicMock(user_data={}))

        update.message.reply_text.assert_called_once_with(DEFAULT_REPLY)

    def test_custom_event_text_is_saved_and_budget_is_requested(self):
        update = self.update("юбилей")
        context = MagicMock(user_data={"awaiting_custom_event": True})

        handle_messages(update, context)

        assert context.user_data["event"] == "юбилей"
        assert "awaiting_custom_event" not in context.user_data
        assert "сумму" in update.message.reply_text.call_args.kwargs["text"]

    def test_unexpected_errors_reach_the_global_error_handler(self, monkeypatch):
        import bot.handlers.start_handlers as module

        def broken(update, context):
            raise RuntimeError("bug")

        monkeypatch.setattr(module, "process_order_step", broken)
        context = MagicMock(user_data={"order_step": "name"})

        with pytest.raises(RuntimeError):
            handle_messages(self.update(), context)
