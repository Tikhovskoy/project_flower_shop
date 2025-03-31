class InvalidPhoneError(Exception):
    """Неверный номер телефона."""


class InvalidDateTimeError(Exception):
    """Неверная дата и время."""


class OrderSaveError(Exception):
    """Ошибка при сохранении заказа."""


class ConsultationSaveError(Exception):
    """Ошибка при сохранении консультации."""


class MissingRequiredFieldError(Exception):
    """Обязательное поле отсутствует."""


class UnknownOrderStepError(Exception):
    """Неизвестный шаг в процессе оформления заказа."""


class MissingOrderDataError(Exception):
    """Отсутствует структура заказа в context.user_data."""


class EmptyBouquetListError(Exception):
    """Пустой список букетов для отображения."""
