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
from core.core import core
from api_rest.rest import *





class AdminHandler:

    async def stats(self, request):
        """ 
            Return list of all annotation's databases and, for each, the list of availables versions and the list of their fields for the latest version
        """
        result = await core.admin.stats()
        return rest_success(result)



