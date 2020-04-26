from base64 import b64encode

import pytest

from main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    yield app.test_client()


def test_thing(client):
    response = client.post("/hook", json={"service": "animelab", "show": "Black"})

    assert response.status == "200 OK"


def test_redis(client):
    response = client.get("/redis")

    assert response.status == "401 UNAUTHORIZED"

    response = client.get(
        "/redis", headers={"Authorization": b"Basic " + b64encode(b"username:password")}
    )

    assert response.status == "200 OK"
