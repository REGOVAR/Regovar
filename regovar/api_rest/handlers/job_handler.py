#!env/python3
# coding: utf-8
try:
    import ipdb
except ImportError:
    pass



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

    #@staticmethod
    #def format_job_json(job_json):
        #if not isinstance(job_json, dict): return job_json
        #if "logs" in job_json.keys():
            #logs = []
            #for l in job_json["logs"]:
                #logs.append("http://{}/dl/job{}".format(HOST_P, l[len(JOBS_DIR):]))
            #job_json["logs"] = logs        
        #return job_json
    
    
    @user_role('Authenticated')
    def list(self, request):
        return rest_success(core.jobs.list())


    @user_role('Authenticated')
    def delete(self, request):
        job_id = request.match_info.get('job_id', "")
        try:
            return rest_success(check_local_path(core.jobs.delete(job_id).to_json()))
        except Exception as error:
            return rest_error("Unable to delete the job (id={}) : {}".format(job_id, error.msg))


    @user_role('Authenticated')
    def get(self, request):
        job_id = request.match_info.get('job_id', -1)
        job = Job.from_id(job_id, 1)
        if not job:
            return rest_error("Unable to find the job (id={})".format(job_id))
        result = job.to_json()
        return rest_success(check_local_path(result))




    @user_role('Authenticated')
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
                await core.notify_all_co({"action": "job_updated", "data" : job.to_json(["id", "update_date", "status", "progress_value", "progress_label", "logs"])})
            
        except Exception as ex:
            return rest_error("Unable to update information for the jobs with id {}. {}".format(job_id, ex))

        return rest_success(check_local_path(job.to_json()))




    @user_role('Authenticated')
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
        project_id = data["project_id"]
        # Create the job 
        try:
            job = core.jobs.new(project_id, pipe_id, name, config, inputs_ids)
        except Exception as ex:
            return rest_error("Error occured when initializing the new job. {}".format(ex))
        if job is None:
            return rest_error("Unable to create a new job.")
        job.init(1)
        return rest_success(check_local_path(job.to_json()))


    @user_role('Authenticated')
    def pause(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        try:
            core.jobs.pause(job_id)
            job = Job.from_id(job_id)
        except Exception as ex:
            return rest_error("Unable to pause the job {}. {}".format(job.id, ex))
        return rest_success(check_local_path(job.to_json()))


    @user_role('Authenticated')
    def start(self, request):
        job_id  = request.match_info.get('job_id', -1)
        try:
            core.jobs.start(job_id)
            job = Job.from_id(job_id)
        except Exception as ex:
            return rest_error("Unable to start the job {}. {}".format(job.id, ex))
        return rest_success(check_local_path(job.to_json()))


    @user_role('Authenticated')
    def cancel(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        try:
            core.jobs.stop(job_id)
            job = Job.from_id(job_id)
        except Exception as ex:
            return rest_error("Unable to stop the job {}. {}".format(job_id, ex))
        return rest_success(check_local_path(job.to_json()))


    @user_role('Authenticated')
    def monitoring(self, request):
        job_id  = request.match_info.get('job_id',  -1)
        try:
            job = core.jobs.monitoring(job_id)
        except Exception as ex:
            return rest_error("Unable to retrieve monitoring info for the jobs with id={}. {}".format(job_id, ex))
        if job:
            return rest_success(check_local_path(job.to_json()))
        return rest_error("Unable to get monitoring information for the job {}.".format(job_id))


    @user_role('Administrator')
    def finalize(self, request):
        job_id  = request.match_info.get('job_id', -1)
        try:
            core.jobs.finalize(job_id)
            job = Job.from_id(job_id)
        except Exception as ex:
            return rest_error("Unable to finalize the job {}. {}".format(job_id, ex))
        job = Job.from_id(job_id)
        return rest_success(check_local_path(job.to_json()))


    @user_role('Authenticated')
    def delete(self, request):
        job_id  = request.match_info.get('job_id', -1)
        
        try:
            result = core.jobs.delete(job_id)
        except Exception as ex:
            return rest_error("Error occured when trying to delete the analysis with id=" + str(analysis_id), exception=ex)
        return rest_success(check_local_path(result.to_json())) 



