import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
LOG_FILE = "bot.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(LOG_PATH, maxBytes=500_000, backupCount=5)
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%d-%m-%Y %H:%M:%S"
)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def log_validation_error(context: str, exception: Exception):
    logger.warning(f"[Валидация] {context} — {exception}")


def log_unexpected_error(context: str, exception: Exception):
    logger.error(f"[Ошибка] {context} — {exception}")
