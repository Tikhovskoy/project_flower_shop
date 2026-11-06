import pytest


@pytest.mark.parametrize("url", ["/api/orders/", "/api/bouquets/", "/api/compositions/"])
def test_browsable_api_renders_in_browser(admin_client_api, order, bouquet, composition, url):
    """Без rest_framework в INSTALLED_APPS HTML-вид API падал с TemplateDoesNotExist."""
    response = admin_client_api.get(url, HTTP_ACCEPT="text/html")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/html")


@pytest.mark.django_db
def test_composition_list_does_not_crash(client, composition):
    """У композиции нет поля price: фильтр по нему раньше ронял список с 500."""
    response = client.get("/api/compositions/")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == [composition.name]
