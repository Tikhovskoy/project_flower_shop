import pytest
from rest_framework.test import APIClient

from bot.models import Bouquet, Composition, Consultation, Order


@pytest.fixture
def make_bouquet(db):
    def make(name="Букет", price=1000, **kwargs):
        return Bouquet.objects.create(name=name, price=price, **kwargs)

    return make


@pytest.fixture
def make_composition(db):
    def make(name="Композиция", event="birthday", bouquets=(), **kwargs):
        composition = Composition.objects.create(name=name, event=event, **kwargs)
        composition.bouquets.set(bouquets)
        return composition

    return make


@pytest.fixture
def bouquet(db):
    return Bouquet.objects.create(name="Облако", price=990, description="Хризантемы")


@pytest.fixture
def composition(db, bouquet):
    composition = Composition.objects.create(name="Свадебная классика", event="wedding")
    composition.bouquets.add(bouquet)
    return composition


@pytest.fixture
def order(db):
    return Order.objects.create(
        customer_name="Анна Тестова",
        phone_number="+79990001122",
        delivery_address="ул. Тестовая, 1",
    )


@pytest.fixture
def consultation(db):
    return Consultation.objects.create(name="Иван Тестов", phone_number="+79990003344")


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def user_client(db, django_user_model):
    """Обычный авторизованный пользователь без прав персонала."""
    user = django_user_model.objects.create_user(username="client", password="x")
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def admin_client_api(db, django_user_model):
    """Администратор (is_staff), для которого API открыт целиком."""
    admin = django_user_model.objects.create_superuser(username="boss", password="x")
    client = APIClient()
    client.force_authenticate(admin)
    return client
