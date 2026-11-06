import pytest

pytestmark = pytest.mark.django_db


def names(response):
    return sorted(item["name"] for item in response.json())


@pytest.fixture
def catalog(make_bouquet, make_composition):
    cheap = make_bouquet("Дешёвый", 450)
    mid = make_bouquet("Средний", 1000)
    upper = make_bouquet("Дорогой", 1500)
    hidden = make_bouquet("Снят", 700, is_available=False)
    make_composition("ДР недорогие", "birthday", [cheap, mid])
    make_composition("ДР дорогие", "birthday", [upper])
    make_composition("Свадьба", "wedding", [mid, upper])
    make_composition("Скрытая", "school", [hidden], is_available=False)


class TestBouquetFilters:
    url = "/api/bouquets/"

    def test_without_filters_returns_everything(self, anon_client, catalog):
        assert len(anon_client.get(self.url).json()) == 4

    def test_min_price(self, anon_client, catalog):
        response = anon_client.get(self.url, {"min_price": 1000})
        assert names(response) == ["Дорогой", "Средний"]

    def test_max_price(self, anon_client, catalog):
        response = anon_client.get(self.url, {"max_price": 700})
        assert names(response) == ["Дешёвый", "Снят"]

    def test_price_range_is_inclusive(self, anon_client, catalog):
        response = anon_client.get(self.url, {"min_price": 450, "max_price": 1000})
        assert names(response) == ["Дешёвый", "Снят", "Средний"]

    def test_exact_price_still_works(self, anon_client, catalog):
        assert names(anon_client.get(self.url, {"price": 1500})) == ["Дорогой"]

    @pytest.mark.parametrize("value", ["true", "True", "1"])
    def test_is_available_truthy_spellings(self, anon_client, catalog, value):
        response = anon_client.get(self.url, {"is_available": value})
        assert names(response) == ["Дешёвый", "Дорогой", "Средний"]

    @pytest.mark.parametrize("value", ["false", "False", "0"])
    def test_is_available_falsy_spellings(self, anon_client, catalog, value):
        assert names(anon_client.get(self.url, {"is_available": value})) == ["Снят"]

    @pytest.mark.parametrize("param", ["min_price", "max_price"])
    def test_non_numeric_price_is_a_validation_error(self, anon_client, catalog, param):
        response = anon_client.get(self.url, {param: "дёшево"})

        assert response.status_code == 400
        assert param in response.json()


class TestCompositionFilters:
    url = "/api/compositions/"

    def test_without_filters_returns_everything(self, anon_client, catalog):
        assert len(anon_client.get(self.url).json()) == 4

    def test_event(self, anon_client, catalog):
        response = anon_client.get(self.url, {"event": "birthday"})
        assert names(response) == ["ДР дорогие", "ДР недорогие"]

    def test_unknown_event_is_a_validation_error(self, anon_client, catalog):
        response = anon_client.get(self.url, {"event": "pirate-party"})

        assert response.status_code == 400
        assert "event" in response.json()

    @pytest.mark.parametrize("value", ["true", "1"])
    def test_is_available_truthy_spellings_agree_with_bouquets(self, anon_client, catalog, value):
        response = anon_client.get(self.url, {"is_available": value})
        assert names(response) == ["ДР дорогие", "ДР недорогие", "Свадьба"]

    @pytest.mark.parametrize("value", ["false", "0"])
    def test_is_available_falsy_spellings(self, anon_client, catalog, value):
        assert names(anon_client.get(self.url, {"is_available": value})) == ["Скрытая"]

    def test_min_price_looks_at_bouquets_of_composition(self, anon_client, catalog):
        response = anon_client.get(self.url, {"min_price": 1500})
        assert names(response) == ["ДР дорогие", "Свадьба"]

    def test_max_price_looks_at_bouquets_of_composition(self, anon_client, catalog):
        response = anon_client.get(self.url, {"max_price": 450})
        assert names(response) == ["ДР недорогие"]

    def test_composition_with_several_matching_bouquets_is_listed_once(self, anon_client, catalog):
        response = anon_client.get(self.url, {"min_price": 450, "max_price": 1000})

        # «ДР недорогие» и «Свадьба» подходят сразу двумя букетами, но в ответе по одному разу;
        # «Скрытая» подходит букетом за 700, фильтр цены наличие композиции не учитывает
        assert names(response) == ["ДР недорогие", "Свадьба", "Скрытая"]
        assert len(response.json()) == 3

    def test_filters_can_be_combined(self, anon_client, catalog):
        response = anon_client.get(self.url, {"event": "birthday", "min_price": 1500})
        assert names(response) == ["ДР дорогие"]

    def test_ordering_is_still_available(self, anon_client, catalog):
        response = anon_client.get(self.url, {"ordering": "-name"})

        assert [item["name"] for item in response.json()] == sorted(names(response), reverse=True)
