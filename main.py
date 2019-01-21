import os
import json
import logging
from typing import Optional

import bcrypt
import requests
from redis import StrictRedis
from dotenv import load_dotenv
from flask import request, render_template, redirect, url_for, jsonify, Flask, flash

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

REDIS_URL = os.environ["REDIS_URL"]
LOGIN_REQUIRED = "", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'}

REDIS = StrictRedis.from_url(REDIS_URL)


@app.route("/hook", methods=["POST"])
def hook():
    service = request.json["service"]
    show = request.json["show"]

    REDIS.publish("watch", json.dumps({"service": service, "show": show}))

    return "", 200


@app.route("/redis")
def redis():
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

    return jsonify({"redis_endpoint": REDIS_URL})
