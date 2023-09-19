import os
from flask import Flask, redirect
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from loguru import logger
from sqlalchemy import event
from sqlalchemy.engine import Engine

os.makedirs(os.getenv("FEDIVERSE_SAFETY_IMGDIR"), exist_ok=True)
cache = None
APP = Flask(__name__)
APP.wsgi_app = ProxyFix(APP.wsgi_app, x_for=1)

SQLITE_MODE = os.getenv("USE_SQLITE", "0") == "1"

if SQLITE_MODE:
    logger.warning("Using SQLite for database")
    APP.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fedi_safety_api.db"
    APP.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "isolation_level": None,
    }
else:
    if os.getenv('POSTGRES_URI') is None:
        raise Exception("Please set the POSTGRES_URI env var")
    APP.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('POSTGRES_URI')
    APP.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_size": 50,
        "max_overflow": -1,
    }

APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(APP)
db.init_app(APP)

if not SQLITE_MODE:
    with APP.app_context():
        logger.debug("pool size = {}".format(db.engine.pool.size()))
elif SQLITE_MODE == 1:
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()
        logger.info("Set pragma to wal")

logger.init_ok("Fedi Safety Database", status="Started")

# Allow local workstation run
if cache is None:
    cache_config = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 300
    }
    cache = Cache(config=cache_config)
    cache.init_app(APP)
    logger.init_warn("Flask Cache", status="SimpleCache")

