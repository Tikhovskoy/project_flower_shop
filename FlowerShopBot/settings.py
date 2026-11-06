from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()
# Локально настройки читаются из .env, в проде — из переменных окружения.
# Уже заданные переменные окружения файлом .env не перезаписываются.
env.read_env(BASE_DIR / '.env')


def optional_int(name):
    """Целое число из окружения или None, если переменная не задана или пуста."""
    raw = env.str(name, default='').strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ImproperlyConfigured(f'{name} должен быть целым числом, получено: {raw!r}') from exc


def csv_list(name, default):
    """Список из значения через запятую; пробелы вокруг элементов отбрасываются."""
    return [item.strip() for item in env.list(name, default=default) if item.strip()]


DEBUG = env.bool('DEBUG', default=False)

SECRET_KEY = env.str('SECRET_KEY', default='')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            'Не задан SECRET_KEY. При DEBUG=False он обязателен: '
            'python -c "from django.core.management.utils import get_random_secret_key; '
            'print(get_random_secret_key())"'
        )
    # Только для разработки: ключ живёт до перезапуска, сессии при этом сбрасываются.
    SECRET_KEY = get_random_secret_key()

ALLOWED_HOSTS = csv_list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = csv_list('CSRF_TRUSTED_ORIGINS', default=[])

# Telegram-бот
TELEGRAM_TOKEN = env.str('TELEGRAM_TOKEN', default='')
COURIER_ID = optional_int('COURIER_ID')
FLORIST_ID = optional_int('FLORIST_ID')

# Продакшен за HTTPS: включается одной переменной HTTPS_ONLY=True
if env.bool('HTTPS_ONLY', default=False):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Сервер за обратным прокси, который сам терминирует TLS и ставит X-Forwarded-Proto
if env.bool('TRUST_PROXY_SSL_HEADER', default=False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'django_filters',

    'bot',
    'multiselectfield',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'FlowerShopBot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'FlowerShopBot.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Asia/Krasnoyarsk'

USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    # Закрыто по умолчанию: открытый доступ нужно выдавать явно в самой вьюхе
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}
