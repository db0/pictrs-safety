import os
from datetime import datetime, timedelta

class Worker():
    last_check_in = None
    
    def __init__(self):
        self.check_in()

    def check_in(self):
        self.last_check_in = datetime.utcnow()
    
    def is_stale(self):
        threshold = int(os.getenv("MISSING_WORKER_THRESHOLD", 5))
        # When threshold is 0, the worker is never stale
        if threshold == 0:
            return False
        return self.last_check_in < datetime.utcnow() - timedelta(seconds=threshold)

worker = Worker()