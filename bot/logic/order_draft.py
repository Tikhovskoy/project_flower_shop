from dataclasses import dataclass
from datetime import datetime

from bot.exceptions import InvalidDateTimeError, InvalidPhoneError
from bot.logging_tools import log_validation_error

from .validators import normalize_datetime, normalize_phone


@dataclass
class OrderDraft:
    """Заказ, который пользователь собирает по шагам в диалоге с ботом."""

    bouquet_id: int
    bouquet_name: str
    price: int
    status: str = "accepted"
    card_text: str = ""
    customer_name: str = ""
    delivery_address: str = ""
    phone_number: str = ""
    delivery_time: datetime | None = None

    @classmethod
    def from_bouquet(cls, bouquet) -> "OrderDraft":
        return cls(bouquet_id=bouquet.id, bouquet_name=bouquet.name, price=bouquet.price)

    def add_card_text(self, card_text: str) -> "OrderDraft":
        self.card_text = card_text
        return self

    def set_contact_info(
        self,
        customer_name: str,
        address: str,
        phone: str,
        delivery_time: str | datetime,
    ) -> "OrderDraft":
        """Проверяет телефон и время, и только после этого записывает контакты.

        При ошибке валидации черновик остаётся нетронутым.
        """
        try:
            normalized_phone = normalize_phone(phone)
        except InvalidPhoneError as error:
            log_validation_error("Ошибка normalize_phone", error)
            raise

        normalized_time = normalize_datetime(delivery_time)
        if normalized_time is None:
            log_validation_error(
                "normalize_datetime вернул None", ValueError(f"Невалидная дата: {delivery_time!r}")
            )
            raise InvalidDateTimeError(
                "Неверный формат времени доставки. Пример: '2025-03-27T14:00'."
            )

        self.customer_name = customer_name
        self.delivery_address = address
        self.phone_number = normalized_phone
        self.delivery_time = normalized_time
        return self

    def courier_message(self) -> str:
        """Текст сообщения курьеру со всеми подробностями заказа."""
        text = (
            "🚚 Новый заказ!\n\n"
            f"💐 Букет: {self.bouquet_name}\n"
            f"💰 Цена: {self.price}₽\n"
            f"👤 Получатель: {self.customer_name}\n"
            f"🏡 Адрес: {self.delivery_address}\n"
            f"📅 Время доставки: {self.delivery_time.strftime('%d.%m %H:%M')}\n"
            f"📞 Телефон: {self.phone_number}\n"
        )
        if self.card_text:
            text += f"\n💌 Открытка: {self.card_text}"
        return text
