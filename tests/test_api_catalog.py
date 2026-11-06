import pytest


@pytest.mark.django_db
def test_composition_list_does_not_crash(client, composition):
    """У композиции нет поля price: фильтр по нему раньше ронял список с 500."""
    response = client.get("/api/compositions/")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == [composition.name]
