#!env/python3
# coding: utf-8
import ipdb; 


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
 





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# API/MISC HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class ApiHandler:
    def __init__(self):
        pass

    def welcom(self, request):
        
        # Retrieve github informations
        response = requests.get("https://api.github.com/repos/REGOVAR/QRegovar/milestones")
        data = False
        if response.ok:
            data = json.loads(response.content.decode())


        result = {
            "api_url": HOST_P,
            "version": core.version,
            "db_version": core.db_version,
            "website" : "http://regovar.org",
            "analyses": self.get_all_analyses(),
            "subjects": self.get_all_subjects(),
            "samples": self.get_all_samples(),
            "projects": self.get_all_projects(),
            "panels": self.get_all_panels(),
            "pipelines": self.get_all_pipelines(),
            "jobs": self.get_all_jobs(),
            "tools": self.get_all_tools(),
            "last_analyses": self.get_last_analyses(),
            "last_subjects" : self.get_last_subjects(),
            "last_events": [],
            "references" : [{"id": ref[0], "name": ref[1]} for ref in core.annotations.ref_list.items()],
            "milestones" : data
        }
        return rest_success(result)



    def config(self, request):
        return rest_success({
            "version" : core.version,
            "db_version": core.db_version,
            "host" : HOST_P,
            "pagination_default_range": RANGE_DEFAULT,
            "pagination_max_range": RANGE_MAX
            })
    
    def get_tools(self, request):
        return rest_success(self.get_tools_list())
    
    
    
    @aiohttp_jinja2.template('api_test.html')
    def api(self, request):
        return {
            "version" : core.version,
            "hostname" : HOST_P,
            "file_public_fields" : ", ".join(File.public_fields)
        }
    
    
    def get_all_analyses(self):
        """
            Lazy loading all analysis to init data of Client
        """
        sql = "SELECT id, project_id, name, comment, create_date, update_date, reference_id, status FROM analysis"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "project_id": res.project_id,
                "name": res.name,
                "comment": res.comment,
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat(),
                "reference_id": res.reference_id,
                "status": res.status
            })
        return result
    def get_all_subjects(self):
        """
            Lazy loading all subjects to init data of Client
        """
        sql = "SELECT id, identifier, firstname, lastname, sex, family_number, dateofbirth, comment, create_date, update_date FROM subject"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "identifier": res.identifier,
                "firstname": res.firstname,
                "lastname": res.lastname,
                "sex": res.sex,
                "family_number": res.family_number,
                "dateofbirth": res.dateofbirth.isoformat() if res.dateofbirth else None,
                "comment": res.comment,
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat()
            })
        return result
    def get_all_samples(self):
        """
            Lazy loading all samples to init data of Client
        """
        sql = "SELECT id, subject_id, name, comment, is_mosaic, file_id, loading_progress, reference_id, status FROM sample ORDER BY id"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "subject_id": res.subject_id,
                "name": res.name,
                "comment": res.comment,
                "status": res.status,
                "is_mosaic": res.is_mosaic,
                "file_id": res.file_id,
                "loading_progress": res.loading_progress,
                "reference_id": res.reference_id
            })
        return result
    def get_all_projects(self):
        """
            Lazy loading all projects to init data of Client
        """
        sql = "SELECT p.id, p.name, p.comment, p.parent_id, p.is_folder, p.create_date, p.update_date, array_agg(a.id) as analyses FROM project p LEFT JOIN analysis a ON a.project_id=p.id where not is_sandbox GROUP BY p.id, p.name, p.comment, p.parent_id, p.is_folder, p.create_date, p.update_date ORDER BY p.parent_id, p.name"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "name": res.name,
                "comment": res.comment,
                "parent_id": res.parent_id,
                "is_folder": res.is_folder,
                "analyses": res.analyses,
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat()
            })
        return result
    def get_all_panels(self):
        """
            Lazy loading all panels to init data of Client
        """
        sql = "SELECT id, name, description, owner, create_date, update_date, shared FROM panel ORDER BY id"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "name": res.name,
                "description": res.description,
                "owner": res.owner,
                "shared": res.shared,
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat()
            })
        return result
    def get_all_pipelines(self):
        """
            Lazy loading all panels to init data of Client
        """
        sql = "SELECT id, name, type, status, description, version, image_file_id, starred, installation_date FROM pipeline ORDER BY id"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "name": res.name,
                "description": res.description,
                "type": res.type,
                "status": res.status,
                "version": res.version,
                "image_file_id": res.image_file_id,
                "starred": res.starred,
                "installation_date": res.installation_date.isoformat()
            })
        return result
    def get_all_jobs(self):
        """
            Lazy loading all jobs to init data of Client
        """
        sql = "SELECT id, pipeline_id, project_id, name, comment, create_date, update_date, status, progress_value, progress_label FROM job ORDER BY id"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "pipeline_id": res.pipeline_id,
                "project_id": res.project_id,
                "name": res.name,
                "comment": res.comment,
                "status": res.status,
                "progress_value": res.progress_value,
                "progress_label": res.progress_label,
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat()
            })
        return result
    def get_all_tools(self):
        """
            Lazy loading all installed tools to export/import files on Regovar server
        """
        result = { "exporters" : [], "reporters" : [] }
        exporters = core.exporters.copy()
        for t in exporters: 
            if "mod" in exporters[t]: 
                exporters[t].pop("mod")
            result["exporters"].append(exporters[t])
        reporters = core.reporters.copy()
        for t in reporters: 
            if "mod" in reporters[t]: 
                reporters[t].pop("mod")
            result["reporters"].append(reporters[t])
        return result
    
    
    def get_last_analyses(self):
        """
            Return last analyses
        """
        sql = "SELECT id FROM analysis WHERE project_id > 0 ORDER BY update_date DESC LIMIT 10"
        result = [res.id for res in execute(sql)]
        return result
    
    def get_last_subjects(self):
        """
            Return last subjects
        """
        sql = "SELECT id FROM subject ORDER BY update_date DESC LIMIT 10"
        result = [res.id for res in execute(sql)]
        return result

    
    