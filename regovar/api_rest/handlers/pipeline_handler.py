#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp

import aiohttp_jinja2
import tarfile
import datetime
import time
import uuid
import subprocess


from aiohttp import web, MultiDict
from urllib.parse import parse_qsl


from config import *
from core.framework.common import *
from core.framework.tus import *
from core.model import *
from core.core import core
from api_rest.rest import *




def format_pipeline_json(pipe_json):
    if "image_file" in pipe_json.keys():
        pipe_json["image_file"] = format_file_json(pipe_json["image_file"] )
    if "documents" in pipe_json.keys():
        docs = []
        for doc in pipe_json["documents"]:
            docs.append("http://{}/dl/pipe/{}/{}".format(HOST_P, pipe_json["id"], os.path.basename(doc)))
        pipe_json["documents"] = docs
    if "jobs" in pipe_json.keys():
        jobs = []
        for job in pipe_json["jobs"]:
            jobs.append(format_job_json(job))
        pipe_json["jobs"] = jobs
    if "path" in pipe_json.keys():
        pipe_json.pop("path")
    return pipe_json



class PipelineHandler:
    def __init__(self):
        pass

    def list(self, request):
        fields, query, order, offset, limit = process_generic_get(request.query_string, Pipeline.public_fields)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('sublvl', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Pipeline.count(),
            "range_max"    : RANGE_MAX,
        }
        pipes = core.pipelines.get(fields, query, order, offset, limit, depth)
        return rest_success([p.to_json() for p in pipes], range_data)


    def get(self, request):
        pipe_id = request.match_info.get('pipe_id', -1)
        pipe = Pipeline.from_id(pipe_id, -1)
        if not pipe:
            return rest_error("No pipeline with id ".format(pipe_id))

        pipe = pipe.to_json(Pipeline.public_fields)
        return rest_success(format_pipeline_json(pipe))


    def install(self, request):
        file_id = request.match_info.get('file_id', -1)
        container_type = request.match_info.get('container_type', -1)
        if container_type not in CONTAINERS_CONFIG.keys():
            return rest_error("Container manager of type {} not supported by the server.".format(container_type))
        file = File.from_id(file_id)
        if not file:
            return rest_error("Unable to find file with id {}.".format(file_id))
        if file.status not in ["uploading", "uploaded", "checked"]:
            return rest_error("File status is {}, this file cannot be used as pipeline image (status shall be \"uploading\", \"uploaded\" or \"checked\"".format(file_id))
        
        p = core.pipelines.install_init_image_local(file.path, False, {"type" : container_type})
        try:
            if core.pipelines.install(p.id, asynch=False):
                return rest_success(pipe.to_json())
        except RegovarException as ex:
            return rest_error(str(ex))
        return rest_error("Error occured during installation of the pipeline.")


    async def install_json(self, request):
        params = await request.json()
        # TO DO 
        return rest_error("Not implemented")


    def delete(self, request):
        pipe_id = request.match_info.get('pipe_id', -1)
        try:
            pipe = core.pipelines.delete(pipe_id, False)
        except Exception as ex:
            # TODO : manage error
            return rest_error("Unable to delete the pipeline with id {} : {}".format(pipe_id, str(ex)))
        return rest_success(pipe)




 
