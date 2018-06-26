 
#!env/python3
# coding: utf-8
try:
    import ipdb
except ImportError:
    pass



import os
import json
import aiohttp
import datetime
import time


from aiohttp import web

from config import *
from core.framework.common import *
from core.framework.tus import *
from core.model import *
from api_rest.rest import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# SUBJECT HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 





class SubjectHandler:



    @user_role('Authenticated')
    def list(self, request):
        """
            Get list of all subjects
        """
        subjects = core.subjects.list()
        return rest_success([check_local_path(s) for s in subjects])


        
    
    @user_role('Authenticated')
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
        return rest_success(check_local_path(subject.to_json()))
        
       
    @user_role('Authenticated') 
    def get(self, request):
        """
            Get details about the subject
        """
        subject_id = request.match_info.get('subject_id', -1)
        subject = Subject.from_id(subject_id, 1)
        if not subject:
            return rest_error("Unable to find the subject (id={})".format(subject_id))
        return rest_success(check_local_path(subject.to_json()))
        
    
    
    
    @user_role('Authenticated')
    def delete(self, request):
        """
            Delete the subject
        """
        from core.core import core
        subject_id = request.match_info.get('subject_id', -1)
        subject = core.Subject.delete(subject_id, 1)
        if not subject:
            return rest_error("Unable to delete the subject (id={})".format(subject_id))
        return rest_success(check_local_path(subject.to_json()))
    
    
    
    @user_role('Authenticated')
    def events(self, request):
        """
            Get list of events of the subject (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Subject.public_fields)
        subject_id = request.match_info.get('subject_id', -1)
        user_id = None # TODO: retrieve user_id from session
        depth = 0
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Subject.count(),
            "range_max"    : RANGE_MAX,
        }
        events = core.events.list(user_id, fields, query, order, offset, limit, depth)
        return rest_success([check_local_path(e.to_json()) for e in events], range_data)


    @user_role('Authenticated')
    def samples(self, request):
        """
            Get list of subjects of the subject (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Subject.public_fields)
        subject_id = request.match_info.get('subject_id', -1)
        depth = 0
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Subject.count(),
            "range_max"    : RANGE_MAX,
        }
        subjects = core.subjects.get(fields, query, order, offset, limit, depth)
        return rest_success([check_local_path(s.to_json()) for s in subjects], range_data)
    
    
    @user_role('Authenticated')
    def analyses(self, request):
        """
             Get list of tasks (jobs and analyses) of the subject (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Subject.public_fields)
        depth = 0
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
        return rest_success([check_local_path(t.to_json()) for t in tasks], range_data)


    @user_role('Authenticated')
    def files(self, request):
        """
            Get list of subjects of the subject (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Subject.public_fields)
        subject_id = request.match_info.get('subject_id', -1)
        depth = 0
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Subject.count(),
            "range_max"    : RANGE_MAX,
        }
        files = core.files.get(fields, query, order, offset, limit, depth)
        return rest_success([check_local_path(f.to_json()) for f in files], range_data)
    
    











