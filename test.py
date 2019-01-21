from main import app
import pytest


@pytest.fixture
def client():
    app.config["TESTING"] = True

    yield app.test_client()


def test_thing(client):
    client.post("/hook", json={"service": "animelab", "show": "Black"})
