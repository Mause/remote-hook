from base64 import b64encode
from typing import Generator

import pytest
from flask.testing import FlaskClient

from main import app


@pytest.fixture  # type: ignore
def client() -> Generator[FlaskClient, None, None]:
    app.config["TESTING"] = True

    yield app.test_client()


def test_thing(client: FlaskClient) -> None:
    response = client.post("/hook", json={"service": "animelab", "show": "Black"})

    assert response.status == "200 OK"


def test_redis(client: FlaskClient) -> None:
    response = client.get("/redis")

    assert response.status == "401 UNAUTHORIZED"

    response = client.get(
        "/redis", headers={"Authorization": b"Basic " + b64encode(b"username:password")}
    )

    assert response.status == "200 OK"
