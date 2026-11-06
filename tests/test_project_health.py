import importlib

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_migrations_cover_all_model_changes():
    """Если модели изменились без миграции, команда завершится с кодом 1."""
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)


def test_bot_module_imports():
    """Бот должен импортироваться с зафиксированными зависимостями (urllib3, pkg_resources)."""
    importlib.import_module("bot.main_bot")
