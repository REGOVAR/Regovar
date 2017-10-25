 
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
from api_rest.rest import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# SUBJECT HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 





class SubjectHandler:



    def list(self, request):
        """
            Get list of all subjects (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Subject.public_fields)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('depth', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Subject.count(),
            "range_max"    : RANGE_MAX,
        }
        subjects = core.subjects.get(fields, query, order, offset, limit, depth)
        return rest_success([s.to_json() for s in subjects], range_data)


        
    
    async def create_or_update(self, request):
        """
            Create or update a subject with provided data
        """
        from core.core import core
        subject_id = request.match_info.get('subject_id', -1)
        data = await request.json()

        if isinstance(data, str) : data = json.loads(data)
        # If provided by the query parameter, ensure that we use the query subject_id
        if subject_id != -1:
        	data["id"] = subject_id
        # Create or update the subject
        try:
            subject = core.subjects.create_or_update(data)
        except RegovarException as ex:
            return rest_exception(ex)
        if subject is None:
            return rest_error("Unable to create a new subject.")
        return rest_success(subject.to_json())
        
        
    def get(self, request):
        """
            Get details about the subject
        """
        subject_id = request.match_info.get('subject_id', -1)
        subject = Subject.from_id(subject_id, 1)
        if not subject:
            return rest_error("Unable to find the subject (id={})".format(subject_id))
        return rest_success(subject.to_json(Subject.public_fields))
        
    
    
    
    def delete(self, request):
        """
            Delete the subject
        """
        from core.core import core
        subject_id = request.match_info.get('subject_id', -1)
        subject = core.Subject.delete(subject_id, 1)
        if not subject:
            return rest_error("Unable to delete the subject (id={})".format(subject_id))
        return rest_success(subject.to_json(Subject.public_fields))
    
    
    
    def events(self, request):
        """
            Get list of events of the subject (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Subject.public_fields)
        subject_id = request.match_info.get('subject_id', -1)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('depth', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Subject.count(),
            "range_max"    : RANGE_MAX,
        }
        events = core.events.get(fields, query, order, offset, limit, depth)
        return rest_success([e.to_json() for e in events], range_data)


    def samples(self, request):
        """
            Get list of subjects of the subject (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Subject.public_fields)
        subject_id = request.match_info.get('subject_id', -1)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('depth', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Subject.count(),
            "range_max"    : RANGE_MAX,
        }
        subjects = core.subjects.get(fields, query, order, offset, limit, depth)
        return rest_success([s.to_json() for s in subjects], range_data)
    
    
    def analyses(self, request):
        """
             Get list of tasks (jobs and analyses) of the subject (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Subject.public_fields)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('depth', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Subject.count(),
            "range_max"    : RANGE_MAX,
        }
        jobs = core.jobs.get(fields, query, order, offset, limit, depth)
        analyses = core.analyses.get(fields, query, order, offset, limit, depth)
        tasks = array_merge(jobs, analyses)
        return rest_success([t.to_json() for t in tasks], range_data)


    def files(self, request):
        """
            Get list of subjects of the subject (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Subject.public_fields)
        subject_id = request.match_info.get('subject_id', -1)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('depth', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Subject.count(),
            "range_max"    : RANGE_MAX,
        }
        files = core.files.get(fields, query, order, offset, limit, depth)
        return rest_success([f.to_json() for f in files], range_data)
    
    











