#!env/python3
# coding: utf-8
import ipdb


import os
import json



from config import *
from core.framework.common import *
from api_rest.rest import *





class DatabaseHandler:

    def get(self, request):
        ref = request.match_info.get('ref', None)
        
        if not ref:
            return rest_success([r for r in os.listdir(DATABASES_DIR) if os.path.isdir(os.path.join(DATABASES_DIR, r))])

        if os.path.isdir(os.path.join(DATABASES_DIR, ref)):
            result = {db:{
                "size": humansize(os.path.getsize(os.path.join(DATABASES_DIR, ref, db))),
                "bsize" : os.path.getsize(os.path.join(DATABASES_DIR, ref, db)),
                "url" : "http://{}/dl/db/{}/{}".format(HOST_P, ref, db),
                } for db in os.listdir(os.path.join(DATABASES_DIR, ref))}
            return rest_success(result)
        return rest_error("Unknow database reference : {}".format(ref))

