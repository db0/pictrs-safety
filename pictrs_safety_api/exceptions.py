from werkzeug import exceptions as wze
from loguru import logger

class BadRequest(wze.BadRequest):
    def __init__(self, message, log="BadRequest"):
        self.specific = message
        self.log = log

class Forbidden(wze.Forbidden):
    def __init__(self, message, log="Forbidden"):
        self.specific = message
        self.log = log

class Unauthorized(wze.Unauthorized):
    def __init__(self, message, log="Unauthorized"):
        self.specific = message
        self.log = log

class NotFound(wze.NotFound):
    def __init__(self, message, log="NotFound"):
        self.specific = message
        self.log = log

class Locked(wze.Locked):
    def __init__(self, message, log="Locked"):
        self.specific = message
        self.log = log

class TooManyRequests(wze.TooManyRequests):
    def __init__(self, message, log="TooManyRequests"):
        self.specific = message
        self.log = log

class InternalServerError(wze.InternalServerError):
    def __init__(self, message, log="InternalServerError"):
        self.specific = message
        self.log = log
        
class ServiceUnavailable(wze.ServiceUnavailable):
    def __init__(self, message, log="ServiceUnavailable"):
        self.specific = message
        self.log = log
        
def handle_bad_requests(error):
    '''Namespace error handler'''
    if error.log:
        logger.debug(error.log)
    return({'message': error.specific}, error.code)
