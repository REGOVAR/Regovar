#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp
import aiohttp_jinja2
import datetime
import time


from aiohttp import web, MultiDict
from urllib.parse import parse_qsl

from config import *
from core.framework.common import *
from core.framework.tus import *
from core.model import *
from core.core import core
from api_rest.rest import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# SAMPLE HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 





class SampleHandler:
    def list(self, request):
        # Generic processing of the get query
        fields, query, order, offset, limit = process_generic_get(request.query_string, Sample.public_fields)
        # Get range meta data
        range_data = {
            "range_offset": offset,
            "range_limit" : limit,
            "range_total" : Sample.count(),
            "range_max"   : RANGE_MAX,
        }
        # Return result of the query 
        return rest_success(core.samples.get(fields, query, order, offset, limit), range_data)


    def get(self, request):
        sid = request.match_info.get('sample_id', None)
        if sid is None:
            return rest_error("No valid sample id provided")
        sample = Sample.from_id(sid)
        if sample is None:
            return rest_error("No sample found with id="+str(sid))
        return rest_success(sample.to_json())




    def import_from_file(self, request):
        
        file_id = request.match_info.get('file_id', None)
        try:
            result = core.samples.import_from_file(file_id)
        except Exception as ex:
            return rest_error("unable to import samples.".format(ex))
        if result:
            return rest_success([s.to_json() for s in samples])
        return rest_error("unable to import samples from file.")