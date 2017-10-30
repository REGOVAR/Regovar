#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp
import aiohttp_jinja2
import datetime
import time
import uuid

import aiohttp_security
from aiohttp_session import get_session
from aiohttp_security import remember, forget, authorized_userid, permits

import asyncio
import functools
import inspect
from aiohttp import web, MultiDict
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
        
        return rest_success({
            "api_url": HOST_P,
            "title": "Regovar Service API",
            "version": VERSION,
            "website" : "http://regovar.org",
            "last_analyses": self.get_last_analyses(),
            "last_subjects" : self.get_last_subjects(),
            "last_events": [],
            "references" : [{"id": ref[0], "name": ref[1]} for ref in core.annotations.ref_list.items()],
            "default_reference_id": DEFAULT_REFERENCIAL_ID
                
        })



    def config(self, request):
        return rest_success({
            "version" : VERSION,
            "host" : HOST_P,
            "pagination_default_range": RANGE_DEFAULT,
            "pagination_max_range": RANGE_MAX
            })
    
    
    @aiohttp_jinja2.template('api_test.html')
    def api(self, request):
        return {
            "version" : VERSION,
            "hostname" : HOST_P,
            "file_public_fields" : ", ".join(File.public_fields)
            }
    
    
    
    
    
    
    
    def get_last_analyses(self):
        """
            Return last analyses
        """
        result = session().query(Analysis).order_by(Analysis.update_date.desc(), Analysis.name.asc()).limit(10).all()
        for res in result: res.init(1)
        fields = Analysis.public_fields + ["project"]
        return [r.to_json(fields) for r in result]
    
    def get_last_subjects(self):
        """
            Return last subjects
        """
        result = session().query(Subject).order_by(Subject.update_date.desc(), Subject.lastname.asc()).limit(10).all()
        for res in result: res.init(1)
        return [r.to_json() for r in result]

    
    