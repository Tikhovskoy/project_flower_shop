import pytest
from django.core.management import call_command

from bot.models import Bouquet, Composition, Consultation, Order


@pytest.fixture
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.mark.django_db
def test_load_demo_creates_catalog_without_orders(media_root):
    call_command("load_demo", verbosity=0)

    assert Bouquet.objects.count() == 8
    assert Composition.objects.count() == 4
    assert Order.objects.count() == 0
    assert Consultation.objects.count() == 0


@pytest.mark.django_db
def test_load_demo_copies_every_photo_to_media_root(media_root):
    call_command("load_demo", verbosity=0)

    for bouquet in Bouquet.objects.all():
        assert (media_root / bouquet.photo.name).is_file(), bouquet.name


@pytest.mark.django_db
def test_load_demo_covers_every_event_and_budget(media_root):
    call_command("load_demo", verbosity=0)

    events = set(Composition.objects.values_list("event", flat=True))
    assert events == {"birthday", "wedding", "school", "no_reason"}
    assert Bouquet.objects.filter(is_available=False).exists()
    assert Bouquet.objects.filter(price__lte=500).exists()
    assert Bouquet.objects.filter(price__gte=2000, is_available=True).exists()


@pytest.mark.django_db
def test_load_demo_is_idempotent(media_root):
    call_command("load_demo", verbosity=0)
    call_command("load_demo", verbosity=0)

    assert Bouquet.objects.count() == 8
    assert Composition.objects.count() == 4
