import json
import logging
import os
import socket
import time
from functools import lru_cache
from typing import Dict

import bcrypt
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from mause_rpc import client
from pika.connection import URLParameters

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

CLOUD_AMQP = os.environ["CLOUDAMQP_URL"]
LOGIN_REQUIRED = "", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'}


@lru_cache()
def get_client(name:str):
    cl = client.get_client(name, URLParameters(CLOUD_AMQP))
    if not cl._thread.is_alive():
        logging.debug('waiting for client thread to live')
        time.sleep(5)
        assert cl._thread.is_alive(), 'Client thread dead'
    return cl


@app.route('/')
def index():
    return 'Hi'


@app.route("/hook", methods=["POST"])
def hook():
    message = dict(request.json)
    action = message.pop('action')

    logging.info('sending %s to %s', message, action)
    client = get_client(action)
    logging.info('client: %s', client)
    response = client.call(action, **message)
    logging.info('response: %s', response)

    return repr(response), 200


@app.route("/rabbitmq")
def rabbitmq():
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
