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




class JobHandler:
    def __init__(self):
        pass

    def list(self, request):
        fields, query, order, offset, limit = process_generic_get(request.query_string, Job.public_fields)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('sublvl', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Job.count(),
            "range_max"    : RANGE_MAX,
        }
        jobs = core.jobs.get(fields, query, order, offset, limit, depth)
        return rest_success([j.to_json() for j in jobs], range_data)


    def delete(self, request):
        job_id = request.match_info.get('job_id', "")
        try:
            return rest_success(core.jobs.delete(job_id).to_json())
        except Exception as error:
            return rest_error("Unable to delete the job (id={}) : {}".format(job_id, error.msg))


    def get(self, request):
        job_id = request.match_info.get('job_id', -1)
        job = Job.from_id(job_id, 2)
        if not job:
            return rest_error("Unable to find the job (id={})".format(job_id))
        return rest_success(job.to_json(Job.public_fields))


    def download_file(self, job_id, filename, location=JOBS_DIR):
        job = Job.from_id(job_id, 1)
        if job == None:
            return rest_error("Unable to find the job (id={})".format(job_id))
        path = os.path.join(job.path, filename)

        if not os.path.exists(path):
            return rest_error("File not found. {} doesn't exists for the job (id={})".format(filename, job_id))
        content = ""
        if os.path.isfile(path):
            with open(path, 'br') as content_file:
                file = content_file.read()
        return web.Response(
            headers=MultiDict({'Content-Disposition': 'Attachment; filename='+filename}),
            body=file
        )

    def get_olog(self, request):
        job_id = request.match_info.get('job_id', -1)
        return self.download_file(job_id, "logs/out.log")

    def get_elog(self, request):
        job_id = request.match_info.get('job_id', -1)
        return self.download_file(job_id, "logs/err.log")

    def get_plog(self, request):
        job_id = request.match_info.get('job_id', -1)
        return self.download_file(job_id, "logs/core.log")

    def get_olog_tail(self, request):
        job_id = request.match_info.get('job_id', -1)
        return self.download_file(job_id, "logs/out.log")

    def get_elog_tail(self, request):
        job_id = request.match_info.get('job_id', -1)
        return self.download_file(job_id, "logs/err.log")

    def get_plog_tail(self, request):
        job_id = request.match_info.get('job_id', -1)
        return self.download_file(job_id, "logs/core.log")

    def get_io(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        if job_id == -1:
            return rest_error("Id not found")
        job = Job.from_id(job_id, 1)
        if job == None:
            return rest_error("Unable to find the job with id {}".format(job_id))
        result={
            "inputs" : [f.to_json() for f in job.inputs],
            "outputs": [f.to_json() for f in job.outputs],
        }
        return rest_success(result)

    def get_file(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        filename = request.match_info.get('filename', "")
        return self.download_file(job_id, filename)


    async def update_status(self, request):
        # 1- Retrieve data from request
        data = await request.json()
        job_id = request.match_info.get('job_id', -1)
        try:
            if "status" in data.keys():
                core.jobs.set_status(job_id, data["status"])
            job = Job.from_id(job_id)
            job.load(data)
        except Exception as ex:
            return rest_error("Unable to update information for the jobs with id {}. {}".format(job_id, ex))

        return rest_success(job.to_json())




    async def new(self, request):
        # 1- Retrieve data from request
        try:
            data = await request.json()
            data = json.loads(data)
        except Exception as ex:
            return rest_error("Error occured when retriving json data to start new job. {}".format(ex))
        missing = []
        for k in ["pipeline_id", "name", "config", "inputs"]:
            if k not in data.keys(): missing.append(k)
        if len(missing) > 0:
            return rest_error("Following informations are missing to create a new job : {}".format(", ".join(missing)))

        pipe_id = data["pipeline_id"]
        name = data["name"]
        config = data["config"]
        inputs = data["inputs"]
        # Create the job 
        try:
            job = core.jobs.new(pipe_id, name, config, inputs, asynch=True)
        except Exception as ex:
            return rest_error("Error occured when initializing the new job. {}".format(ex))
        if job is None:
            return rest_error("Unable to create a new job.")
        return rest_success(job.to_json())


    def pause(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        try:
            core.jobs.pause(job_id, False)
        except Exception as ex:
            return rest_error("Unable to pause the job {}. {}".format(job.id, ex))
        return rest_success()


    def start(self, request):
        job_id  = request.match_info.get('job_id', -1)
        try:
            core.jobs.start(job_id, False)
        except Exception as ex:
            return rest_error("Unable to start the job {}. {}".format(job.id, ex))
        return rest_success()


    def cancel(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        try:
            core.jobs.stop(job_id, False)
        except Exception as ex:
            return rest_error("Unable to stop the job {}. {}".format(job_id, ex))
        return rest_success()


    def monitoring(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        try:
            job = core.jobs.monitoring(job_id)
        except Exception as ex:
            return rest_error("Unable to retrieve monitoring info for the jobs with id={}. {}".format(job_id, ex))
        if job:
            return rest_success(format_job_json(job, ["id", "pipeline_id", "start_date", "update_date", "status", "progress_value", "progress_label", "inputs_ids", "outputs_ids", "logs", "logs_tails"]))
        return rest_error("Unable to get monitoring information for the job {}.".format(job_id))


    def finalize(self, request):
        job_id  = request.match_info.get('job_id', -1)
        try:
            core.jobs.finalize(job_id, False)
        except Exception as ex:
            return rest_error("Unable to finalize the job {}. {}".format(job_id, ex))
        job = Job.from_id(job_id)
        return rest_success(format_job_json(job))



