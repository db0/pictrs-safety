import fedi_safety_api.apis.v1.base as base
from fedi_safety_api.apis.v1.base import api

api.add_resource(base.Scan, "/scan/<string:pictrs_id>")
api.add_resource(base.Pop, "/pop")
