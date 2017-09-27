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
        if ref_id is None or int(ref_id) not in core.annotations.ref_list.keys() :
            return rest_error("A valid reference id must be provided.")
        ref_id = int(ref_id)

        
        result = { "ref_id": ref_id, "ref_name": core.annotations.ref_list[ref_id], "db": []}


        # First we add db common to all ref (variant info and regovar computed annotation)
        for db_name in core.annotations.db_list[0]["order"]:
            db_data = core.annotations.db_list[0]['db'][db_name].copy()
            dbs = db_data.pop('versions')
            db_data.update({"versions": {}})
            db_data.update({"default": next(iter(dbs.values()))})
            
            for dversion, duid in dbs.items():
                fields = []
                for fuid in  core.annotations.db_map[duid]['fields']:
                    fields.append(core.annotations.fields_map[fuid])
                db_data['versions'][duid] = {'uid' : duid, 'version': dversion, 'fields': fields}
            result["db"].append(db_data)

        # Next add annotations available for the ref
        if ref_id != 0 and ref_id in core.annotations.db_list.keys():
            for db_name in core.annotations.db_list[ref_id]["order"]:
                db_data = core.annotations.db_list[ref_id]['db'][db_name].copy()
                dbs = db_data.pop('versions')
                db_data.update({"versions": {}})
                db_data.update({"default": next(iter(dbs.values()))})
                
                for dversion, duid in dbs.items():
                    fields = []
                    for fuid in core.annotations.db_map[duid]['fields']:
                        fields.append(core.annotations.fields_map[fuid])
                    db_data['versions'][duid] = {'uid' : duid, 'version': dversion, 'fields': fields}
                result["db"].append(db_data)


        return rest_success(result)


    def get_database(self, request):
        """
            Return the annotation database description and the list of available versions
        """
        db_id = request.match_info.get('db_id', -1)
        result = {}
        result.update(core.annotations.db_map[db_id])
        return rest_success(result)


    def get_field(self, request):
        """
            Return the annotation field details
        """
        field_id = request.match_info.get('field_id', -1)
        return rest_success(core.annotations.fields_map[field_id])


    async def delete(self, request):
        """
            Delete an annotations database and all its fields
            User have to take care regarding side effects of this actions on his analysis
        """
        dbuid = request.match_info.get("db_id", None)
        if not await core.annotations.delete(dbuid) :
            return rest_success()
        return rest_error()







    




 
