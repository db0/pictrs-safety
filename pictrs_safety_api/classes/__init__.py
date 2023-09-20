from pictrs_safety_api.flask import db, APP

# Importing for DB creation
from pictrs_safety_api.classes.request import ScanRequest

with APP.app_context():

    db.create_all()