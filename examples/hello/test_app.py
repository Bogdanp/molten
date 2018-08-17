import pytest

from app import app
from molten import testing


@pytest.fixture(scope="session")
def client():
    return testing.TestClient(app)


def test_successful_request(client):
    response = client.get(app.reverse_uri("hello", name="Jim", age=24))
    assert response.status_code == 200
    assert response.json() == "Hello 24 year old named Jim!"


def test_bad_request(client):
    response = client.get(app.reverse_uri("hello", name="Jim", age="invalid"))
    assert response.status_code == 400
    assert response.json() == {"errors": {"age": "invalid int value"}}
