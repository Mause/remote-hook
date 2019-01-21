import os
import logging
from typing import Optional

import requests
from redis import StrictRedis
from dotenv import load_dotenv
from flask import request, render_template, redirect, url_for, jsonify, Flask, flash

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

REDIS_URL = os.environ["REDIS_URL"]
REDIS = StrictRedis.from_url(REDIS_URL)


def autocomplete(text: str) -> Optional[str]:
    result = requests.get(
        "https://www.animelab.com/shows/autocomplete", params={"searchTerms": text}
    ).json()

    if result["suggestions"]:
        return result["suggestions"][0]
    else:
        return None


def send(data):
    ps = redis.pubsub()

    ps.publish("watch", json.dump())



def animelab(show: str) -> None:
    show = autocomplete(show)

    raise Exception(show)


@app.route("/hook", methods=["POST"])
def hook():
    service = request.json["service"]
    show = request.json["show"]

    if service == 'animelab':
        animelab(show)
    else:
        raise Exception()


@app.route("/redis")
def redis():
    auth = request.authorization
    if not auth:
        return LOGIN_REQUIRED

    ok = all(
        [
            auth["username"] == config["CONFIG_USERNAME"],
            bcrypt.checkpw(
                auth["password"].encode(), config["CONFIG_PASSWORD"].encode()
            ),
        ]
    )
    if not ok:
        return LOGIN_REQUIRED

    return jsonify({"redis_endpoint": REDIS_URL})

