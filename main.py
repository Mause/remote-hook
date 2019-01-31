import os
import json
import socket
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
REDIS.execute_command('client setname remotehook')


def get_clients():
    clients = REDIS.execute_command('client list').decode().splitlines()
    return [
        dict(
            pair.split('=')
            for pair in client.split()
        )
        for client in clients
    ]


def get_name(client):
    return client['name'] or client['host'] or client['addr']


@app.route('/')
def index():
    if request.method == 'POST':
        clients = execute('plex', 'electromagnetic girlfriend')
        return f'Tested: {{clients}}', 200
    else:
        clients = get_clients()
        for client in clients:
            ip, _ = client['addr'].split(':')
            try:
                host = socket.gethostbyaddr(ip)
            except socket.herror:
                host = None
            client['host'] = host
        return render_template(
            'index.html',
            clients=clients,
            get_name=get_name
        )


@app.route("/hook", methods=["POST"])
def hook():
    service = request.json["service"]
    show = request.json["show"]

    print(request.json)

    clients = execute(service, show)

    return str(clients), 200


def execute(service, show):
    clients = REDIS.publish("watch", json.dumps({"service": service, "show": show}))
    logging.info('playing "%s" on "%s" on %s clients', show, service, clients)
    return clients


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

