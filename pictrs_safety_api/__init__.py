import os
import socket
from uuid import uuid4

from pictrs_safety_api.logger import logger
from pictrs_safety_api.flask import APP
from pictrs_safety_api.routes import * 
from pictrs_safety_api.apis import apiv1
from pictrs_safety_api.argparser import args
from pictrs_safety_api.consts import PICTRS_SAFETY_VERSION
import hashlib

APP.register_blueprint(apiv1)


@APP.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, apikey, Client-Agent, X-Fields"
    response.headers["Fedi-Safety-API-Node"] = f"{socket.gethostname()}:{args.port}:{PICTRS_SAFETY_VERSION}"
    try:
        etag = hashlib.sha1(response.get_data()).hexdigest()
    except RuntimeError:
        etag = "Runtime Error"
    response.headers["ETag"] = etag
    return response
