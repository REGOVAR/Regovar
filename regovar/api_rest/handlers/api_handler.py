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
 





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# API/MISC HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class ApiHandler:
    def __init__(self):
        pass

    def welcom(self, request):
        
        # Retrieve github informations
        response = requests.get("https://api.github.com/repos/REGOVAR/QRegovar/milestones")
        data = False
        if response.ok:
            data = json.loads(response.content.decode())


        result = {
            "api_url": HOST_P,
            "title": "Regovar Service API",
            "version": core.version,
            "website" : "http://regovar.org",
            "last_analyses": self.get_last_analyses(),
            "last_subjects" : self.get_last_subjects(),
            "last_events": [],
            #"tools" : self.get_tools_list(),
            "references" : [{"id": ref[0], "name": ref[1]} for ref in core.annotations.ref_list.items()],
            "milestones" : data
        }

        return rest_success(result)



    def config(self, request):
        return rest_success({
            "version" : core.version,
            "host" : HOST_P,
            "pagination_default_range": RANGE_DEFAULT,
            "pagination_max_range": RANGE_MAX
            })
    
    def get_tools(self, request):
        return rest_success(self.get_tools_list())
    
    
    
    
    
    
    @aiohttp_jinja2.template('api_test.html')
    def api(self, request):
        return {
            "version" : core.version,
            "hostname" : HOST_P,
            "file_public_fields" : ", ".join(File.public_fields)
            }
    
    
    
    
    def get_tools_list(self):
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
        result = Session().query(Analysis).order_by(Analysis.update_date.desc(), Analysis.name.asc()).limit(10).all()
        for res in result: res.init(0)
        fields = Analysis.public_fields + ["project"]
        return [r.to_json(fields) for r in result]
    
    
    def get_last_subjects(self):
        """
            Return last subjects
        """
        result = Session().query(Subject).order_by(Subject.update_date.desc(), Subject.lastname.asc()).limit(10).all()
        for res in result: res.init(0)
        return [r.to_json() for r in result]

    
    