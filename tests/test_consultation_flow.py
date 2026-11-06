import pytest

from bot.exceptions import InvalidPhoneError
from bot.logic.consultation_flow import request_consultation
from bot.models import Consultation

pytestmark = pytest.mark.django_db


def test_saves_consultation_with_normalized_phone():
    result = request_consultation("8 (913) 123-45-67", user_id=42, name="Иван")

    consultation = Consultation.objects.get()
    assert consultation.phone_number == "+79131234567"
    assert (consultation.user_id, consultation.name, consultation.status) == (42, "Иван", "new")
    assert result == {"phone": "+79131234567", "user_id": 42, "name": "Иван", "status": "new"}


def test_name_defaults_to_anonymous():
    request_consultation("+79131234567", user_id=1)

    assert Consultation.objects.get().name == "(аноним)"


@pytest.mark.parametrize("phone", ["", "abc", "12345"])
def test_invalid_phone_is_rejected_and_nothing_is_saved(phone):
    with pytest.raises(InvalidPhoneError):
        request_consultation(phone, user_id=1)

    assert Consultation.objects.count() == 0


def test_invalid_phone_is_logged_as_validation_error(caplog):
    with pytest.raises(InvalidPhoneError), caplog.at_level("WARNING", logger="bot_logger"):
        request_consultation("12345", user_id=1)

    assert "Валидация" in caplog.text
