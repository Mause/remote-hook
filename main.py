import os
import json
from functools import lru_cache
import socket
import logging
from typing import Dict

import bcrypt
import requests
from redis import StrictRedis
from dotenv import load_dotenv
from flask import request, jsonify, Flask

from mause_rpc import client

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

CLOUD_AMQP = os.environ["CLOUD_AMQP"]
LOGIN_REQUIRED = "", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'}


@lru_cache()
def get_client(name:str):
    return client.get_client(name, CLOUD_AMQP)


@app.route('/')
def index():
    return 'Hi'


@app.route("/hook", methods=["POST"])
def hook():
    rq = dict(request.json)
    print(rq)

    action = rq.pop('action', 'watch')

    response = execute(action, rq)

    return repr(response), 200


def execute(action: str, message: Dict):
    logging.info('sending %s to %s', message, action)
    response = get_client(action).call(action, message)


@app.route("/rabbitm")
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
