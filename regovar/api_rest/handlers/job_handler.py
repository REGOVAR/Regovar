#!env/python3
# coding: utf-8
import ipdb; 


import os
import json

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




class JobHandler:
    def __init__(self):
        pass

    @staticmethod
    def format_job_json(job_json):
        if not isinstance(job_json, dict): return job_json
        if "logs" in job_json.keys():
            logs = []
            for l in job_json["logs"]:
                logs.append("http://{}/dl/job{}".format(HOST_P, l[len(JOBS_DIR):]))
            job_json["logs"] = logs        
        return job_json
    
    
    def list(self, request):
        return rest_success(core.jobs.list())


    def delete(self, request):
        job_id = request.match_info.get('job_id', "")
        try:
            return rest_success(self.format_job_json(core.jobs.delete(job_id).to_json()))
        except Exception as error:
            return rest_error("Unable to delete the job (id={}) : {}".format(job_id, error.msg))


    def get(self, request):
        from api_rest.handlers.file_handler import FileHandler
        from api_rest.handlers.pipeline_handler import PipelineHandler
        job_id = request.match_info.get('job_id', -1)
        job = Job.from_id(job_id, 2)
        if not job:
            return rest_error("Unable to find the job (id={})".format(job_id))
        result = job.to_json(Job.public_fields)
        formated_inputs = [FileHandler.format_file_json(f) for f in result["inputs"]]
        formated_outputs = [FileHandler.format_file_json(f) for f in result["outputs"]]
        formated_pipeline = PipelineHandler.format_pipeline_json(result["pipeline"])
        result["inputs"] = formated_inputs
        result["outputs"] = formated_outputs
        result["pipeline"] = formated_pipeline
        return rest_success(self.format_job_json(result))




    async def update_status(self, request):
        # 1- Retrieve data from request
        data = await request.json()
        job_id = request.match_info.get('job_id', -1)
        try:
            job = Job.from_id(job_id)
            new_status = data.pop("status") if "status" in data else None
            job.load(data)
            if new_status:
                print("JOB STATUS CHANGE: " + new_status)
                core.jobs.set_status(job, new_status)
            else:
                core.notify_all({"action": "job_updated", "data" : job.to_json()})
            
        except Exception as ex:
            return rest_error("Unable to update information for the jobs with id {}. {}".format(job_id, ex))

        return rest_success(self.format_job_json(job.to_json()))




    async def new(self, request):
        # 1- Retrieve data from request
        try:
            data = await request.json()
            if isinstance(data, str) : data = json.loads(data)
        except Exception as ex:
            return rest_error("Error occured when retriving json data to start new job. {}".format(ex))
        missing = []
        for k in ["pipeline_id", "name", "config", "inputs_ids"]:
            if k not in data.keys(): missing.append(k)
        if len(missing) > 0:
            return rest_error("Following informations are missing to create a new job : {}".format(", ".join(missing)))

        pipe_id = data["pipeline_id"]
        name = data["name"]
        config = data["config"]
        inputs_ids = data["inputs_ids"]
        # Create the job 
        try:
            job = core.jobs.new(pipe_id, name, config, inputs_ids, asynch=True)
        except Exception as ex:
            return rest_error("Error occured when initializing the new job. {}".format(ex))
        if job is None:
            return rest_error("Unable to create a new job.")
        return rest_success(self.format_job_json(job.to_json()))


    def pause(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        try:
            core.jobs.pause(job_id, False)
            job = Job.from_id(job_id)
        except Exception as ex:
            return rest_error("Unable to pause the job {}. {}".format(job.id, ex))
        return rest_success(self.format_job_json(job.to_json()))


    def start(self, request):
        job_id  = request.match_info.get('job_id', -1)
        try:
            core.jobs.start(job_id, False)
            job = Job.from_id(job_id)
        except Exception as ex:
            return rest_error("Unable to start the job {}. {}".format(job.id, ex))
        return rest_success(self.format_job_json(job.to_json()))


    def cancel(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        try:
            core.jobs.stop(job_id, False)
            job = Job.from_id(job_id)
        except Exception as ex:
            return rest_error("Unable to stop the job {}. {}".format(job_id, ex))
        return rest_success(self.format_job_json(job.to_json()))


    def monitoring(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        try:
            job = core.jobs.monitoring(job_id)
        except Exception as ex:
            return rest_error("Unable to retrieve monitoring info for the jobs with id={}. {}".format(job_id, ex))
        if job:
            return rest_success(self.format_job_json(job.to_json(["id", "update_date", "status", "progress_value", "progress_label", "logs", "monitoring"])))
        return rest_error("Unable to get monitoring information for the job {}.".format(job_id))


    def finalize(self, request):
        job_id  = request.match_info.get('job_id', -1)
        try:
            core.jobs.finalize(job_id, False)
            job = Job.from_id(job_id)
        except Exception as ex:
            return rest_error("Unable to finalize the job {}. {}".format(job_id, ex))
        job = Job.from_id(job_id)
        return rest_success(self.format_job_json(job))



