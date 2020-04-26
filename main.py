import json
import logging
import os
import socket
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
    return client.get_client(name, URLParameters(CLOUD_AMQP))


@app.route('/')
def index():
    return 'Hi'


@app.route("/hook", methods=["POST"])
def hook():
    message = dict(request.json)
    action = message.pop('action')

    logging.info('sending %s to %s', message, action)
    response = get_client(action).call(action, message)

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
