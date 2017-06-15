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
        depth = int(MultiDict(parse_qsl(request.query_string)).get('depth', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Sample.count(),
            "range_max"    : RANGE_MAX,
        }
        # Return result of the query.
        samples = core.samples.get(fields, query, order, offset, limit, depth)
        return rest_success([s.to_json() for s in samples], range_data)


    def get(self, request):
        sid = request.match_info.get('sample_id', None)
        if sid is None:
            return rest_error("No valid sample id provided")
        sample = Sample.from_id(sid)
        if sample is None:
            return rest_error("No sample found with id="+str(sid))
        return rest_success(sample.to_json())




    async def import_from_file(self, request):
        params = get_query_parameters(request.query_string, ["subject_id", "analysis_id"])
        file_id = request.match_info.get('file_id', None)
        
        
        try:
            samples = await core.samples.import_from_file(file_id)
        except Exception as ex:
            print(ex)
            return rest_error("Import error : enable to import samples. ".format(str(ex)))
        if samples:
            for s in samples:
                if params["subject_id"]: 
                    s.subject_id = params["subject_id"]
                else:
                    # TODO: create new empty subject and associate it to the sample
                    log("TODO : link sample {} to new empty subject".format(s.id))
                if params["analysis_id"]: 
                    AnalysisSample.new(s.id, params["analysis_id"])
            return rest_success([s.to_json() for s in samples])
        
        return rest_error("unable to import samples from file.")
    
    
    
    
    
    