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
            "version": "alpha",
            "format_supported": ["json"],
            "website" : "core.org"
        })



    def config(self, request):
        return rest_success({
            "host": HOST_P,
            "pagination_default_range": RANGE_DEFAULT,
            "pagination_max_range": RANGE_MAX,
            "export_modules": annso.export_modules, 
            "import_modules": annso.import_modules,
            "report_modules": annso.report_modules
            })