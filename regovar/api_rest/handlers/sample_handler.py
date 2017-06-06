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
    def get_samples(self, request):
        # Generic processing of the get query
        fields, query, order, offset, limit = process_generic_get(request.query_string, Sample.public_fields)
        # Get range meta data
        range_data = {
            "range_offset": offset,
            "range_limit" : limit,
            "range_total" : core.samples.total(),
            "range_max"   : RANGE_MAX,
        }
        # Return result of the query 
        return rest_success(core.samples.get(fields, query, order, offset, limit), range_data)


    def get_sample(self, request):
        sid = request.match_info.get('sample_id', None)
        if sid is None:
            return rest_error("No valid sample id provided")
        sample = Sample.from_id(sid)
        if sample is None:
            return rest_error("No sample found with id="+str(sid))
        return rest_success(sample.to_json())


    def get_details(self, request):
        db_name = request.match_info.get('db_name', None)
        if db_name is None:
            return rest_error("No database name provided")

        return rest_success({"database": db_name})


    # # Resumable download implement the TUS.IO protocol.
    # def tus_config(self, request):
    #     return tus_manager.options(request)

    # async def tus_upload_init(self, request):
    #     return tus_manager.creation(request)

    # def tus_upload_resume(self, request):
    #     return tus_manager.resume(request)

    # async def tus_upload_chunk(self, request):
    #     result = await tus_manager.patch(request)
    #     return result

    # def tus_upload_delete(self, request):
    #     return tus_manager.delete_file(request) 
