#!env/python3
# coding: utf-8
try:
    import ipdb
except ImportError:
    pass



import os
import json
import aiohttp

import aiohttp_jinja2
import tarfile
import datetime
import time
import uuid
import subprocess


from aiohttp import web
from urllib.parse import parse_qsl


from config import *
from core.framework.common import *
from core.framework.tus import *
from core.model import *
from core.core import core
from api_rest.rest import *



    




class PipelineHandler:
    def __init__(self):
        pass

    #@staticmethod
    #def format_pipeline_json(pipe_json):
        #if not isinstance(pipe_json, dict): return pipe_json
        #if "documents" in pipe_json.keys() and isinstance(pipe_json["documents"], dict):
            #docs = {}
            #for doc in pipe_json["documents"].keys():
                #docs[doc] = "http://{}/dl/pipe/{}/{}".format(HOST_P, pipe_json["id"], os.path.basename(pipe_json["documents"][doc]))
            #pipe_json["documents"] = docs

        #if "path" in pipe_json.keys():
            #pipe_json.pop("path")
        #return pipe_json

    @user_role('Authenticated')
    def list(self, request):
        """
            List all pipelines
        """
        pipes = core.pipelines.list()
        return rest_success(check_local_path(pipes))


    @user_role('Authenticated')
    def get(self, request):
        pipe_id = request.match_info.get('pipe_id', -1)
        pipe = Pipeline.from_id(pipe_id, -1)
        if not pipe:
            return rest_error("No pipeline with id {}".format(pipe_id))

        pipe = pipe.to_json(Pipeline.public_fields)
        return rest_success(check_local_path(pipe))


    @user_role('Administrator')
    def install(self, request):
        file_id = request.match_info.get('file_id', -1)
        file = File.from_id(file_id)
        if not file:
            return rest_error("Unable to find file with id {}.".format(file_id))
        if file.status not in ["uploading", "uploaded", "checked"]:
            return rest_error("File status is {}, this file cannot be used as pipeline image (status shall be \"uploading\", \"uploaded\" or \"checked\"".format(file_id))
        
        p = core.pipelines.install_init_image_local(file.path, False)
        try:
            pipe = core.pipelines.install(p.id, asynch=False)
            if pipe:
                return rest_success(check_local_path(pipe.to_json()))
        except RegovarException as ex:
            return rest_error(str(ex))
        return rest_error("Error occured during installation of the pipeline.")


    @user_role('Administrator')
    async def install_json(self, request):
        params = await request.json()
        # TO DO 
        return rest_error("Not implemented")


    @user_role('Administrator')
    def delete(self, request):
        pipe_id = request.match_info.get('pipe_id', -1)
        try:
            pipe = core.pipelines.delete(pipe_id, False)
        except Exception as ex:
            # TODO : manage error
            return rest_error("Unable to delete the pipeline with id {} : {}".format(pipe_id, str(ex)))
        return rest_success(check_local_path(pipe))




 
