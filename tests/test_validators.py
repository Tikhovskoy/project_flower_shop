from datetime import UTC, datetime, timedelta, timezone

import pytest
import pytz
from freezegun import freeze_time

from bot.exceptions import InvalidPhoneError
from bot.logic.validators import normalize_datetime, normalize_phone, validate_phone

KRASNOYARSK = pytz.timezone("Asia/Krasnoyarsk")

# 27 марта 2025, 10:00 по Красноярску (UTC+7)
NOW_IN_KRASNOYARSK = "2025-03-27T03:00:00Z"


class TestNormalizePhone:
    @pytest.mark.parametrize(
        "raw",
        [
            "+79131234567",
            "89131234567",
            "8 (913) 123-45-67",
            "+7 913 123 45 67",
            "79131234567",
            "9131234567",
            "  +7 (913) 123-45-67  ",
        ],
    )
    def test_russian_formats_become_e164(self, raw):
        assert normalize_phone(raw) == "+79131234567"

    def test_foreign_numbers_are_kept(self):
        assert normalize_phone("+1 202 555 0143") == "+12025550143"

    @pytest.mark.parametrize("raw", ["", "abc", "123", "+7999", "+7 000 000 00 00"])
    def test_garbage_raises_invalid_phone_error(self, raw):
        with pytest.raises(InvalidPhoneError):
            normalize_phone(raw)


class TestValidatePhone:
    @pytest.mark.parametrize("raw", ["+79131234567", "89131234567", "+12025550143"])
    def test_valid_numbers(self, raw):
        assert validate_phone(raw) is True

    @pytest.mark.parametrize("raw", ["", "abc", "123", "+7999"])
    def test_invalid_numbers_return_false_instead_of_raising(self, raw):
        assert validate_phone(raw) is False


@freeze_time(NOW_IN_KRASNOYARSK)
class TestNormalizeDatetime:
    def test_naive_datetime_gets_krasnoyarsk_timezone(self):
        result = normalize_datetime(datetime(2025, 3, 28, 14, 0))

        assert result.utcoffset() == timedelta(hours=7)
        assert (result.hour, result.minute) == (14, 0)

    def test_aware_datetime_is_returned_unchanged(self):
        moment = datetime(2025, 3, 28, 14, 0, tzinfo=UTC)

        assert normalize_datetime(moment) is moment

    @pytest.mark.parametrize("raw", ["2025-03-28T14:00", "2025-03-28 14:00", "  2025-03-28T14:00 "])
    def test_iso_format(self, raw):
        assert normalize_datetime(raw) == KRASNOYARSK.localize(datetime(2025, 3, 28, 14, 0))

    def test_russian_format(self):
        assert normalize_datetime("28.03.2025 14:00") == KRASNOYARSK.localize(
            datetime(2025, 3, 28, 14, 0)
        )

    @pytest.mark.parametrize("raw", ["сегодня 14:00", "Сегодня 14:00", " сегодня   14:00"])
    def test_today_with_time(self, raw):
        assert normalize_datetime(raw) == KRASNOYARSK.localize(datetime(2025, 3, 27, 14, 0))

    def test_tomorrow_with_time(self):
        assert normalize_datetime("завтра 09:30") == KRASNOYARSK.localize(
            datetime(2025, 3, 28, 9, 30)
        )

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "когда-нибудь",
            "вчера 10:00",
            "сегодня",
            "сегодня 25:00",
            "завтра 12:61",
            "31.02.2025 10:00",
        ],
    )
    def test_unparseable_input_returns_none(self, raw):
        assert normalize_datetime(raw) is None

    def test_iso_with_utc_offset_is_accepted(self):
        result = normalize_datetime("2025-03-28T14:00+07:00")

        assert result == datetime(2025, 3, 28, 14, 0, tzinfo=timezone(timedelta(hours=7)))

    def test_iso_with_zulu_suffix_keeps_the_moment(self):
        result = normalize_datetime("2025-03-28T07:00:00Z")

        assert result == datetime(2025, 3, 28, 7, 0, tzinfo=UTC)

    @pytest.mark.parametrize("value", [None, 12345, 1.5])
    def test_non_string_input_returns_none_instead_of_crashing(self, value):
        assert normalize_datetime(value) is None
