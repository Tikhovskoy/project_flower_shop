import importlib

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import clear_url_caches

import FlowerShopBot.urls


@pytest.fixture
def reload_urls():
    """Пересобирает urlpatterns под изменённые настройки и возвращает всё как было."""

    def reload():
        clear_url_caches()
        importlib.reload(FlowerShopBot.urls)

    yield reload
    reload()


@pytest.fixture
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    (tmp_path / "photo.txt").write_text("лепестки", encoding="utf-8")
    return tmp_path


def test_media_is_not_served_by_django_in_production_mode(settings, media_root, reload_urls):
    settings.DEBUG = False
    settings.SERVE_MEDIA = False
    reload_urls()

    assert Client().get("/media/photo.txt").status_code == 404


def test_media_is_served_when_explicitly_enabled(settings, media_root, reload_urls):
    settings.DEBUG = False
    settings.SERVE_MEDIA = True
    reload_urls()

    response = Client().get("/media/photo.txt")

    assert response.status_code == 200
    assert b"".join(response.streaming_content).decode("utf-8") == "лепестки"


def test_media_cannot_escape_media_root(settings, media_root, reload_urls):
    settings.DEBUG = False
    settings.SERVE_MEDIA = True
    reload_urls()

    response = Client().get("/media/../manage.py")

    assert response.status_code in (400, 404)


def test_admin_static_is_served_without_debug(settings, tmp_path):
    """Под gunicorn статику админки отдаёт WhiteNoise из STATIC_ROOT."""
    settings.DEBUG = False
    settings.STATIC_ROOT = tmp_path / "static"
    call_command("collectstatic", interactive=False, verbosity=0)

    response = Client().get("/static/admin/css/base.css")

    assert response.status_code == 200
    assert "css" in response["Content-Type"]
