 
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
from core.model import *
from api_rest.rest import *








class EventHandler:
    def list(self, request):
        """
            Get list of all events (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Project.public_fields)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('depth', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Project.count(),
            "range_max"    : RANGE_MAX,
        }
        projects = core.projects.get(fields, query, order, offset, limit, depth)
        return rest_success([p.to_json() for p in projects], range_data)
        
    
    async def new(self, request):
        """
            Create new event with provided data
        """
        from core.core import core
        data = await request.json()
        is_folder = data["is_folder"]
        name = data["name"]
        parent_id = data["parent_id"]
        # Create the project
        try:
            project = core.projects.new(name, is_folder, parent_id)
        except Exception as ex:
            return rest_error("Error occured when creating the new project. {}".format(ex))
        if project is None:
            return rest_error("Unable to create a new project.")
        return rest_success(project.to_json())
        
        
    def get(self, request):
        """
            Get details about the project
        """
        project_id = request.match_info.get('project_id', -1)
        project = Project.from_id(job_id, 2)
        if not project:
            return rest_error("Unable to find the project (id={})".format(project_id))
        return rest_success(project.to_json(Project.public_fields))
        
        
        
    async def edit(self, request):
        """
            Edit project meta data
        """
        data = await request.json()
        # Create the project
        return rest_error("To be implemented")
    
    
    
    def delete(self, request):
        """
            Delete the project
        """
        project_id = request.match_info.get('project_id', -1)
        project = Project.delete(project_id, 2)
        if not project:
            return rest_error("Unable to delete the project (id={})".format(project_id))
        return rest_success(project.to_json(Project.public_fields))
    
    











