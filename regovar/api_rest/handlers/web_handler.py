#!env/python3
# coding: utf-8

# Developers additional dependencies
try:
    import ipdb
except ImportError:
    pass



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
# Web regovar "light viewer" HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class WebHandler:
    def __init__(self):
        pass

    
    #@user_role('Authenticated')
    @aiohttp_jinja2.template('web_home.html')
    def home(self, request):
        # Get message
        sql = "SELECT value FROM parameter WHERE key = 'message'"
        message = None
        for res in execute(sql):
            message = json.loads(res.value)

        return {
            "hostname" : HOST_P,
            "error": None,
            "path": [],
            "message": message
        }


    @aiohttp_jinja2.template('web_search.html')
    def search(self, request):
        searchQuery = request.match_info.get('query', None)
        if searchQuery is None :
            return { "hostname" : HOST_P, "error": "Nothing to search...", "path": ["search"] }
        try:
            result = core.search.search(searchQuery)
        except RegovarException as ex:
            return { "hostname" : HOST_P, "error": "Error occured while trying to search", "path": ["search"] }
        return {
            "hostname" : HOST_P,
            "error": None,
            "path": ["search"],
            "data": result
        }


    @aiohttp_jinja2.template('web_info.html')
    def info(self, request):
        asset_type = request.match_info.get('type', "unknow")
        asset_id = request.match_info.get('id', None)

        if asset_type == "file":
            file = File.from_id(asset_id)
            if file:
                pass

        pass


    @aiohttp_jinja2.template('web_viewer.html')
    def viewer(self, request):
        asset_id = request.match_info.get('id', None)
        file = File.from_id(asset_id)
        ftype = "txt"
        result = []
        try:
            if file and file.status in ['uploaded', 'checked']:
                with open(file.path, "r") as f:
                    for l in range(1000):
                        result.append(next(f))
        except Exception as ex:
            if not isinstance(ex, StopIteration):
                # file is not a txt file, parse binary
                ftype = "bin"

        return {
            "hostname" : HOST_P,
            "error": None,
            "path": ["view"],
            "type": ftype,
            "data": result
        }
