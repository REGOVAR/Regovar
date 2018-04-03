#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp
import aiohttp_jinja2
import datetime
import time
import requests

import aiohttp_security
from aiohttp_session import get_session
from aiohttp_security import remember, forget, authorized_userid, permits

import asyncio
import functools
import inspect
from aiohttp import web
from urllib.parse import parse_qsl

from config import *
from core.framework.common import *
from core.model import *
from core.core import core
from api_rest.rest import *
from api_rest.handlers import PipelineHandler
 





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# API/MISC HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class ApiHandler:
    def __init__(self):
        pass

    
    @user_role('Authenticated')
    def welcom(self, request):
        """
            Get all data to init/refresh data client side
            /!\ Result answer may be heavy
        """

        result = {
            "analyses": core.analyses.list(),
            "subjects": core.subjects.list(),
            "samples": core.samples.list(),
            "projects": core.projects.list(),
            "panels": core.panels.list(),
            "pipelines": core.pipelines.list(),
            "jobs": core.jobs.list(),
            "users": core.users.list(),
            "last_events": core.events.list(),
            "last_analyses": self.get_last_analyses(),
            "last_subjects" : self.get_last_subjects(),
            "references" : [{"id": ref[0], "name": ref[1]} for ref in core.annotations.ref_list.items()]
        }
        return rest_success(check_local_path(result))



    def config(self, request):
        """
            Return the server configuration and planned milestones for server and official client
        """
        # Retrieve github informations
        response = requests.get("https://api.github.com/repos/REGOVAR/QRegovar/milestones")
        cdata = False
        if response.ok:
            cdata = json.loads(response.content.decode())
        response = requests.get("https://api.github.com/repos/REGOVAR/Regovar/milestones")
        sdata = False
        if response.ok:
            sdata = json.loads(response.content.decode())

        return rest_success({
            "website": "http://regovar.org",
            "version" : core.version,
            "db_version": core.db_version,
            "host" : HOST_P,
            "pagination_default_range": RANGE_DEFAULT,
            "pagination_max_range": RANGE_MAX,
            "tools": self.get_all_tools(),
            "server_milestones" : sdata,
            "client_milestones" : cdata
            })
    
    
    
    @aiohttp_jinja2.template('api_test.html')
    def api(self, request):
        return {
            "version" : core.version,
            "hostname" : HOST_P,
            "file_public_fields" : ", ".join(File.public_fields)
        }
    











    def get_all_tools(self):
        """
            Lazy loading all installed tools to export/import files on Regovar server
        """
        result = { "exporters" : [], "reporters" : [] }
        exporters = core.exporters.copy()
        for t in exporters: 
            if "mod" in exporters[t]: 
                exporters[t].pop("mod")
            result["exporters"].append(exporters[t])
        reporters = core.reporters.copy()
        for t in reporters: 
            if "mod" in reporters[t]: 
                reporters[t].pop("mod")
            result["reporters"].append(reporters[t])
        return result
    
    
    def get_last_analyses(self):
        """
            Return last analyses
        """
        sql = "(SELECT 'analysis' AS type, id, update_date FROM analysis WHERE project_id > 0 ORDER BY update_date DESC LIMIT 10)  UNION (SELECT 'pipeline' AS type, id, update_date FROM job ORDER BY update_date DESC LIMIT 10) ORDER BY update_date DESC"
        result = [{"id": res.id, "type": res.type} for res in execute(sql)]
        return result
    
    def get_last_subjects(self):
        """
            Return last subjects
        """
        sql = "SELECT id FROM subject ORDER BY update_date DESC LIMIT 10"
        result = [res.id for res in execute(sql)]
        return result

    
    