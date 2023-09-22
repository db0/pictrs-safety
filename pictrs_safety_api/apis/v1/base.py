import os
import time
import json
from uuid import uuid4
from PIL import Image
from io import BytesIO
from werkzeug.datastructures import FileStorage
from flask import request, send_file
from flask_restx import Namespace, Resource, reqparse
from pictrs_safety_api.flask import cache, db
from loguru import logger
from pictrs_safety_api.classes.request import ScanRequest
from pictrs_safety_api.database import functions as database
from pictrs_safety_api import exceptions as e
from pictrs_safety_api import enums
from pictrs_safety_api.classes.worker import worker

api = Namespace('v1', 'API Version 1' )

from pictrs_safety_api.apis.models.v1 import Models

models = Models(api)

handle_bad_request = api.errorhandler(e.BadRequest)(e.handle_bad_requests)
handle_forbidden = api.errorhandler(e.Forbidden)(e.handle_bad_requests)
handle_unauthorized = api.errorhandler(e.Unauthorized)(e.handle_bad_requests)
handle_not_found = api.errorhandler(e.NotFound)(e.handle_bad_requests)
handle_too_many_requests = api.errorhandler(e.TooManyRequests)(e.handle_bad_requests)
handle_internal_server_error = api.errorhandler(e.InternalServerError)(e.handle_bad_requests)
handle_service_unavailable = api.errorhandler(e.ServiceUnavailable)(e.handle_bad_requests)

# Simple global to track when a worker last checked in
worker_last_checkin = None

# Used to for the flask limiter, to limit requests per url paths
def get_request_path():
    # logger.info(dir(request))
    return f"{request.remote_addr}@{request.method}@{request.path}"


class Scan(Resource):
    post_parser = api.parser()
    post_parser.add_argument("Content-Type", type=str, required=False, help="The file's media type.", location="headers")
    post_parser.add_argument('file', location='files', type=FileStorage, required=False)

    @api.expect(post_parser)
    def post(self,pictrs_id):
        '''Scan an image
        '''
        # I don't get why this is not using the import from earlier...
        from pictrs_safety_api import exceptions as e
        if pictrs_id == "IPADDR":
            if request.remote_addr not in json.loads(os.getenv("KNOWN_PICTRS_IPS","[]"))\
                    and not self.is_private_ip(request.remote_addr):
                raise e.Unauthorized("You are not authorized to use this service", f"Unauthorized IP: {request.remote_addr}")
        elif pictrs_id not in json.loads(os.getenv("KNOWN_PICTRS_IDS", "[]")):
            raise e.Unauthorized("You are not authorized to use this service", f"Unauthorized ID: {pictrs_id}")
        if worker.is_stale():
            logger.warning(f"Returning OK due to stale worker. Last seen: {worker.last_check_in}")
            return {"message": "Worker Stale"}, 200 
        scan_threshold = int(os.getenv("SCAN_BYPASS_THRESHOLD", 10))
        if scan_threshold > 0 and database.count_waiting_scan_requests() > scan_threshold:
            logger.warning(f"Returning OK due to full queue. Queue: {database.count_waiting_scan_requests()}")
            return {"message": "Queue Full"}, 200 
        self.args = self.post_parser.parse_args()
        file = self.args["file"]
        if not file:
            img_data = BytesIO(request.data)
            filetext = request.headers["Content-Type"].split('/',1)[1]
            upload_filename = f"{uuid4()}.{filetext}"
            if not img_data:
                raise e.BadRequest("No file provided","Missing file")
        else:
            upload_filename = file.filename
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if not upload_filename.lower().endswith(tuple(allowed_extensions)):
                raise e.BadRequest("Invalid file format",f"Invalid file format: {upload_filename}")
            img_data = BytesIO(file.read())
        self.filename = f"{os.getenv('FEDIVERSE_SAFETY_IMGDIR')}/{upload_filename}"
        try:
            img = Image.open(img_data)
            img.save(self.filename)
            new_request = ScanRequest(
                image = upload_filename
            )
            db.session.add(new_request)
            db.session.commit()
            retries = 0
            while new_request.state in [enums.State.PROCESSING, enums.State.WAITING]:
                db.session.refresh(new_request)
                retries += 1
                logger.debug([new_request,new_request.state])
                if retries > int(os.getenv('FEDIVERSE_SAFETY_TIME_THRESHOLD', 120)):
                    os.remove(self.filename)
                    db.session.delete(new_request)
                    db.session.commit()
                    logger.warning("Scanning timeout")
                    return {"message": "Could not scan request in reasonable amount of time. Returning OK"}, 200
                time.sleep(1)
            os.remove(self.filename)
            if new_request.state == enums.State.FAULTED:
                db.session.delete(new_request)
                db.session.commit()
                logger.warning("Faulted request. Returning OK")
                return {"message": "Faulted request. Returning OK"}, 200 
            if new_request.state == enums.State.DONE:
                if new_request.is_csam == True:
                    db.session.delete(new_request)
                    db.session.commit()
                    logger.warning("Potential CSAM Image detected")
                    return {"message": "Potential CSAM Image detected"}, 406
                else: 
                    db.session.delete(new_request)
                    db.session.commit()
                    logger.debug("Image OK")
                    return {"message": "Image OK"}, 200 
            else:
                db.session.delete(new_request)
                db.session.commit()
                logger.error(f"Image with state {new_request.state} detected!")
                return {"message": "Should not be here. Returning OK"},200
        except Exception as err:
            logger.error(f"Exception while processing scan: {err}")
            db.session.delete(new_request)
            db.session.commit()
            return {"message": "Something went wrong internally. Returning OK"}, 200
    
    def is_private_ip(self,remote_addr):
        if remote_addr == "127.0.0.1":
            return True
        if remote_addr.startswith("10"):
            s = remote_addr.split('.')[1]
            if int(s) in range(0,255):
                return True
        if remote_addr.startswith("172"):
            s = remote_addr.split('.')[1]
            if int(s) in range(16,31):
                return True
        if remote_addr.startswith("192"):
            s = remote_addr.split('.')[1]
            if int(s) == 168:
                return True
        return False


class Pop(Resource):
    get_parser = api.parser()
    get_parser.add_argument("apikey", type=str, required=True, help="The auth api key", location="headers")

    @api.expect(get_parser)
    def get(self):
        '''Pick up an image to safety validate
        '''
        # I don't get why this is not using the import from earlier...
        # logger.debug(request.remote_addr)
        self.args = self.get_parser.parse_args()
        if os.getenv("FEDIVERSE_SAFETY_WORKER_AUTH") != self.args.apikey:
            raise e.Forbidden("Access Denied")
        worker.check_in()
        pop: ScanRequest = database.find_waiting_scan_request()
        if not pop:
            return {"message": "Nothing to do"},204
        pop.state = enums.State.PROCESSING
        db.session.commit()
        return send_file(f"{os.getenv('FEDIVERSE_SAFETY_IMGDIR')}/{pop.image}", as_attachment=True, download_name=pop.image)

    post_parser = api.parser()
    post_parser.add_argument("apikey", type=str, required=True, help="The auth api key", location="headers")
    post_parser.add_argument("image", type=str, required=True, help="The image filename", location="json")
    post_parser.add_argument("is_csam", type=bool, required=True, help="Is this image csam?", location="json")
    post_parser.add_argument("is_nsfw", type=bool, required=True, help="Is this image nsfw?", location="json")

    @api.expect(post_parser)
    def post(self):
        '''Submit an image result
        '''
        # I don't get why this is not using the import from earlier...
        self.args = self.post_parser.parse_args()
        if os.getenv("FEDIVERSE_SAFETY_WORKER_AUTH") != self.args.apikey:
            raise e.Forbidden("Access Denied")
        pop: ScanRequest = database.find_scan_request_by_name(self.args.image)
        if not pop:
            raise e.NotFound("No image found waiting for this result.")
        pop.is_csam = self.args.is_csam
        pop.is_nsfw = self.args.is_nsfw
        pop.state = enums.State.DONE
        db.session.commit()
        return {"message": "OK"},201
