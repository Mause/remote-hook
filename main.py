import logging
import os
import time
from concurrent.futures import TimeoutError as FutureTimeoutError
from functools import lru_cache
from typing import Any, Union

import bcrypt
import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from mause_rpc import client
from pika.connection import URLParameters

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

CLOUD_AMQP = os.environ["CLOUDAMQP_URL"]
LOGIN_REQUIRED = "", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'}


@lru_cache
def get_client(name: str) -> client.Client:
    cl = client.get_client(name, URLParameters(CLOUD_AMQP))
    assert cl._thread
    if not cl._thread.is_alive():
        logging.debug('waiting for client thread to live')
        time.sleep(5)
        assert cl._thread.is_alive(), 'Client thread dead'
    return cl


@app.route('/')  # type: ignore
def index() -> str:
    return 'Hi'


@app.route("/hook", methods=["POST"])  # type: ignore
def hook() -> tuple[str, int] | Response:
    message = dict(request.json or {})
    action = message.pop('action', None)
    if not action:
        return jsonify(error='Malformed payload')

    logging.info('sending %s to %s', message, action)
    client = get_client(action)
    logging.info('client: %s', client)
    try:
        response: Any = client.call(action, **message)  # type: ignore
    except FutureTimeoutError as e:
        return jsonify(error='Timeout waiting for rpc response')
    logging.info('response: %s', response)

    return repr(response), 200


@app.route("/rabbitmq")  # type: ignore
def rabbitmq() -> tuple[str, int, dict[str, str]] | Response:
    auth = request.authorization
    if not auth:
        return LOGIN_REQUIRED

    ok = all(
        [
            auth["username"] == os.environ["CONFIG_USERNAME"],
            bcrypt.checkpw(
                auth["password"].encode(), os.environ["CONFIG_PASSWORD"].encode()
            ),
        ]
    )
    if not ok:
        return LOGIN_REQUIRED

    return jsonify({"rabbitmq_endpoint": CLOUD_AMQP})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
