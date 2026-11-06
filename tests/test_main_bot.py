from unittest.mock import MagicMock

import pytest

from bot import main_bot
from bot.handlers.errors import handle_error


def test_refuses_to_start_without_token(settings):
    settings.TELEGRAM_TOKEN = ""

    with pytest.raises(RuntimeError, match="TELEGRAM_TOKEN"):
        main_bot.main()


def test_registers_handlers_and_global_error_handler(settings, monkeypatch):
    settings.TELEGRAM_TOKEN = "123:fake-token"
    updater_class = MagicMock()
    monkeypatch.setattr(main_bot, "Updater", updater_class)

    main_bot.main()

    updater_class.assert_called_once_with(token="123:fake-token")
    dispatcher = updater_class.return_value.dispatcher
    dispatcher.add_error_handler.assert_called_once_with(handle_error)
    assert dispatcher.add_handler.call_count == 9
    updater_class.return_value.start_polling.assert_called_once_with()
