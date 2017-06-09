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
from core.framework.rest import *
from core.framework.tus import *
from core.model import *
from core.core import core
from api_rest.rest import *




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# ANNOTATION DATABASES HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class AnnotationDBHandler:
    def list(self, request):
        """ 
            Return list of genom's referencials supported
        """
        return rest_success(core.annotations.ref_list)


    def get(self, request):
        """ 
            Return list of all annotation's databases and, for each, the list of availables versions and the list of their fields for the latest version
        """
        ref_id = request.match_info.get('ref_id', None)
        if ref_id is None or ref_id not in core.annotations.ref_list.keys():
            ref_id = DEFAULT_REFERENCIAL_ID 

        result = { "ref_id": ref_id, "ref_name": core.annotations.ref_list[ref_id], "db": []}

        for db_name in core.annotations.db_list[ref_id]["order"]:
            db_data = core.annotations.db_list[ref_id]['db'][db_name]
            db_data.update({"selected": next(iter(db_data['versions'].keys()))})
            db_data['fields'] = []
            for fuid in core.annotations.db_map[db_data['versions'][db_data['selected']]]['fields']:
                db_data['fields'].append(core.annotations.fields_map[fuid])

            result["db"].append(db_data)
        #core.annotations.db_list[2]['refGene']['versions'][max(core.annotations.db_list[2]['refGene']['versions'].keys())]

        return rest_success(result)


    def get_database(self, request):
        """
            Return the annotation database description and the list of available versions
        """
        db_id = request.match_info.get('db_id', -1)
        result = {}
        result.update(core.annotations.db_map[db_id])
        result["update"] = result["update"].ctime()
        return rest_success(result)


    def get_field(self, request):
        """
            Return the annotation field details
        """
        field_id = request.match_info.get('field_id', -1)
        return rest_success(core.annotations.fields_map[field_id])








    




 
