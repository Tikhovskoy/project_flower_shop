import pytest

from bot.models import Consultation, Order

DENIED = (401, 403)

PRIVATE_LISTS = ["/api/orders/", "/api/consultations/"]
PRIVATE_DETAILS = ["/api/orders/{order.pk}/", "/api/consultations/{consultation.pk}/"]
CATALOG_LISTS = ["/api/bouquets/", "/api/compositions/"]


class TestAnonymousCannotTouchPrivateData:
    @pytest.mark.parametrize("url", PRIVATE_LISTS)
    def test_cannot_list(self, anon_client, order, consultation, url):
        assert anon_client.get(url).status_code in DENIED

    @pytest.mark.parametrize("template", PRIVATE_DETAILS)
    def test_cannot_read_detail(self, anon_client, order, consultation, template):
        url = template.format(order=order, consultation=consultation)
        assert anon_client.get(url).status_code in DENIED

    @pytest.mark.parametrize("url", PRIVATE_LISTS + ["/api/order/create/"])
    def test_cannot_create(self, db, anon_client, url):
        payload = {"customer_name": "x", "name": "x", "phone_number": "+79990000000"}
        assert anon_client.post(url, payload, format="json").status_code in DENIED
        assert Order.objects.count() == 0
        assert Consultation.objects.count() == 0

    @pytest.mark.parametrize("method", ["put", "patch", "delete"])
    @pytest.mark.parametrize("template", PRIVATE_DETAILS)
    def test_cannot_modify_or_delete(self, anon_client, order, consultation, template, method):
        url = template.format(order=order, consultation=consultation)
        response = getattr(anon_client, method)(url, {"name": "hacked"}, format="json")
        assert response.status_code in DENIED
        assert Order.objects.filter(pk=order.pk).exists()
        assert Consultation.objects.filter(pk=consultation.pk).exists()


class TestRegularUserCannotTouchPrivateData:
    @pytest.mark.parametrize("url", PRIVATE_LISTS)
    def test_cannot_list(self, user_client, order, consultation, url):
        assert user_client.get(url).status_code == 403

    def test_cannot_create_order_via_api(self, user_client):
        response = user_client.post("/api/order/create/", {"customer_name": "x"}, format="json")
        assert response.status_code == 403


class TestAdminHasFullAccessToPrivateData:
    @pytest.mark.parametrize("url", PRIVATE_LISTS)
    def test_can_list(self, admin_client_api, order, consultation, url):
        response = admin_client_api.get(url)
        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.parametrize("template", PRIVATE_DETAILS)
    def test_can_read_detail(self, admin_client_api, order, consultation, template):
        url = template.format(order=order, consultation=consultation)
        assert admin_client_api.get(url).status_code == 200

    def test_can_create_consultation(self, admin_client_api):
        payload = {"name": "Мария", "phone_number": "+79990005566"}
        response = admin_client_api.post("/api/consultations/", payload, format="json")
        assert response.status_code == 201

    def test_can_delete_consultation(self, admin_client_api, consultation):
        response = admin_client_api.delete(f"/api/consultations/{consultation.pk}/")
        assert response.status_code == 204

    def test_can_create_order_via_api(self, admin_client_api):
        payload = {
            "customer_name": "Анна",
            "phone_number": "+79990001122",
            "delivery_address": "ул. Тестовая, 1",
        }
        response = admin_client_api.post("/api/order/create/", payload, format="json")
        assert response.status_code == 201


class TestCatalogIsPublicForReadingOnly:
    @pytest.mark.parametrize("url", CATALOG_LISTS)
    def test_anonymous_can_read(self, anon_client, bouquet, composition, url):
        response = anon_client.get(url)
        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.parametrize("url", CATALOG_LISTS)
    def test_anonymous_cannot_write(self, anon_client, bouquet, composition, url):
        response = anon_client.post(url, {"name": "x", "price": 1}, format="json")
        assert response.status_code in DENIED

    def test_anonymous_cannot_delete_bouquet(self, anon_client, bouquet):
        assert anon_client.delete(f"/api/bouquets/{bouquet.pk}/").status_code in DENIED

    @pytest.mark.parametrize("url", CATALOG_LISTS)
    def test_regular_user_cannot_write(self, user_client, bouquet, composition, url):
        response = user_client.post(url, {"name": "x", "price": 1}, format="json")
        assert response.status_code == 403

    def test_admin_can_create_bouquet(self, admin_client_api):
        response = admin_client_api.post(
            "/api/bouquets/", {"name": "Новый", "price": 1500}, format="json"
        )
        assert response.status_code == 201


def test_endpoints_are_closed_by_default():
    """Любая новая вьюха без явных прав должна требовать вход."""
    from django.conf import settings

    assert settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == [
        "rest_framework.permissions.IsAuthenticated"
    ]
