from unittest.mock import MagicMock

import pytest

from bot.handlers.catalog_handlers import (
    find_bouquets,
    handle_budget_selection,
    handle_full_collection,
    price_range_for,
)


@pytest.mark.parametrize(
    ("choice", "expected"),
    [
        ("500", (0, 500)),
        ("1000", (500, 1000)),
        ("2000", (1500, 2000)),
        ("more", (2000, None)),
        ("any", (0, None)),
    ],
)
def test_budget_buttons_map_to_price_ranges(choice, expected):
    assert price_range_for(choice) == expected


@pytest.mark.django_db
class TestFindBouquets:
    @pytest.fixture
    def shop(self, make_bouquet, make_composition):
        wedding = make_bouquet("Свадебный", 3000)
        birthday = make_bouquet("Именинный", 900)
        make_composition("Свадьба", "wedding", [wedding])
        make_composition("ДР", "birthday", [birthday])

    def test_known_event_uses_its_compositions(self, shop):
        assert [b.name for b in find_bouquets("wedding", 0, None)] == ["Свадебный"]

    def test_event_is_case_insensitive(self, shop):
        assert [b.name for b in find_bouquets("Wedding", 0, None)] == ["Свадебный"]

    def test_free_text_event_falls_back_to_whole_catalog(self, shop):
        assert len(find_bouquets("юбилей у бабушки", 0, None)) == 2

    def test_no_event_means_whole_catalog(self, shop):
        assert len(find_bouquets(None, 0, None)) == 2

    def test_price_range_applies(self, shop):
        assert [b.name for b in find_bouquets(None, 2000, None)] == ["Свадебный"]


def make_update(callback_data):
    update = MagicMock()
    update.callback_query.data = callback_data
    update.callback_query.message.chat_id = 7
    return update


@pytest.mark.django_db
class TestHandlers:
    def test_budget_selection_stores_bouquets_and_shows_first(self, make_bouquet):
        make_bouquet("Первый", 400)
        make_bouquet("Второй", 3000)
        context = MagicMock(user_data={})

        handle_budget_selection(make_update("any"), context)

        assert [b.name for b in context.user_data["bouquets"]] == ["Первый", "Второй"]
        assert context.user_data["current_bouquet"] == 0
        assert context.bot.send_message.called

    def test_empty_range_tells_the_user(self, make_bouquet):
        make_bouquet("Дорогой", 5000)
        update = make_update("500")
        context = MagicMock(user_data={})

        handle_budget_selection(update, context)

        update.callback_query.edit_message_text.assert_called_once()
        assert "bouquets" not in context.user_data

    def test_full_collection_ignores_budget(self, make_bouquet):
        make_bouquet("Дорогой", 5000)
        context = MagicMock(user_data={"event": None})

        handle_full_collection(make_update("show_full_collection"), context)

        assert len(context.user_data["bouquets"]) == 1
