import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from environs import Env

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = ROOT / "FlowerShopBot" / "settings.py"

MANAGED_VARIABLES = [
    "DEBUG",
    "SECRET_KEY",
    "ALLOWED_HOSTS",
    "CSRF_TRUSTED_ORIGINS",
    "TELEGRAM_TOKEN",
    "COURIER_ID",
    "FLORIST_ID",
    "HTTPS_ONLY",
    "TRUST_PROXY_SSL_HEADER",
    "SECURE_HSTS_SECONDS",
    "DATABASE_PATH",
    "MEDIA_ROOT",
    "SERVE_MEDIA",
]

# Длинный случайный ключ, чтобы проходила проверка security.W009
PRODUCTION_SECRET_KEY = "T8m#Xq2$vL9pZr4&Wb7nKd1!Hc5@Ys3^Fg6*Ju0(Ae8)Pt2-Rn4=Vk7+Ox1"


@pytest.fixture
def load_settings(monkeypatch):
    """Выполняет settings.py с чистым окружением; файл .env разработчика не читается."""
    monkeypatch.setattr(Env, "read_env", staticmethod(lambda *args, **kwargs: False))
    for name in MANAGED_VARIABLES:
        monkeypatch.delenv(name, raising=False)

    def load(**env):
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        return runpy.run_path(str(SETTINGS_FILE))

    return load


class TestSecretKeyAndDebug:
    def test_debug_is_off_by_default(self, load_settings):
        assert load_settings(SECRET_KEY="k")["DEBUG"] is False

    def test_missing_secret_key_is_an_error_when_debug_is_off(self, load_settings):
        with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
            load_settings()

    def test_secret_key_comes_from_environment(self, load_settings):
        assert load_settings(SECRET_KEY="from-env")["SECRET_KEY"] == "from-env"

    def test_debug_without_key_gets_a_random_throwaway_key(self, load_settings):
        first = load_settings(DEBUG="True")["SECRET_KEY"]
        second = load_settings(DEBUG="True")["SECRET_KEY"]

        assert len(first) >= 50
        assert first != second

    def test_source_has_no_hardcoded_key(self):
        assert "django-insecure" not in SETTINGS_FILE.read_text(encoding="utf-8")


class TestHostsAndTelegramIds:
    def test_hosts_default_to_localhost(self, load_settings):
        hosts = load_settings(SECRET_KEY="k")["ALLOWED_HOSTS"]
        assert hosts == ["localhost", "127.0.0.1"]

    def test_hosts_are_parsed_from_comma_separated_list(self, load_settings):
        config = load_settings(SECRET_KEY="k", ALLOWED_HOSTS="shop.example.com, www.example.com")
        assert config["ALLOWED_HOSTS"] == ["shop.example.com", "www.example.com"]

    def test_ids_are_parsed_as_integers(self, load_settings):
        config = load_settings(SECRET_KEY="k", COURIER_ID="111", FLORIST_ID="-100222")
        assert (config["COURIER_ID"], config["FLORIST_ID"]) == (111, -100222)

    @pytest.mark.parametrize("value", [None, "", "  "])
    def test_missing_or_blank_ids_become_none(self, load_settings, value):
        env = {"SECRET_KEY": "k"}
        if value is not None:
            env["COURIER_ID"] = value
        assert load_settings(**env)["COURIER_ID"] is None

    def test_garbage_id_is_reported_clearly(self, load_settings):
        with pytest.raises(ImproperlyConfigured, match="COURIER_ID"):
            load_settings(SECRET_KEY="k", COURIER_ID="abc")

    def test_bot_token_comes_from_environment(self, load_settings):
        config = load_settings(SECRET_KEY="k", TELEGRAM_TOKEN="123:abc")
        assert config["TELEGRAM_TOKEN"] == "123:abc"


class TestStoragePaths:
    def test_paths_default_to_project_directory(self, load_settings):
        config = load_settings(SECRET_KEY="k")

        assert config["DATABASES"]["default"]["NAME"] == ROOT / "db.sqlite3"
        assert config["MEDIA_ROOT"] == ROOT / "media"

    def test_paths_come_from_environment(self, load_settings, tmp_path):
        config = load_settings(
            SECRET_KEY="k",
            DATABASE_PATH=str(tmp_path / "data" / "shop.sqlite3"),
            MEDIA_ROOT=str(tmp_path / "files"),
        )

        assert config["DATABASES"]["default"]["NAME"] == tmp_path / "data" / "shop.sqlite3"
        assert config["MEDIA_ROOT"] == tmp_path / "files"

    def test_serving_media_from_django_is_off_by_default(self, load_settings):
        assert load_settings(SECRET_KEY="k")["SERVE_MEDIA"] is False
        assert load_settings(SECRET_KEY="k", SERVE_MEDIA="True")["SERVE_MEDIA"] is True


class TestHttpsSettings:
    def test_https_hardening_is_off_by_default(self, load_settings):
        config = load_settings(SECRET_KEY="k")
        assert "SECURE_SSL_REDIRECT" not in config

    def test_https_only_enables_secure_cookies_redirect_and_hsts(self, load_settings):
        config = load_settings(SECRET_KEY="k", HTTPS_ONLY="True")

        assert config["SECURE_SSL_REDIRECT"] is True
        assert config["SESSION_COOKIE_SECURE"] is True
        assert config["CSRF_COOKIE_SECURE"] is True
        assert config["SECURE_HSTS_SECONDS"] == 31536000

    def test_proxy_header_is_trusted_only_on_request(self, load_settings):
        assert "SECURE_PROXY_SSL_HEADER" not in load_settings(SECRET_KEY="k")
        config = load_settings(SECRET_KEY="k", TRUST_PROXY_SSL_HEADER="True")
        assert config["SECURE_PROXY_SSL_HEADER"] == ("HTTP_X_FORWARDED_PROTO", "https")


def run_manage(*args, **env):
    """Запускает manage.py в отдельном процессе. Переменные заданы явно, поэтому .env не влияет."""
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=ROOT,
        env={**os.environ, "PYTHONUTF8": "1", **env},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_check_deploy_is_clean_with_production_variables():
    result = run_manage(
        "check",
        "--deploy",
        "--fail-level",
        "WARNING",
        DEBUG="False",
        SECRET_KEY=PRODUCTION_SECRET_KEY,
        ALLOWED_HOSTS="shop.example.com",
        HTTPS_ONLY="True",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_manage_py_explains_missing_secret_key():
    result = run_manage("check", DEBUG="False", SECRET_KEY="")

    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr
