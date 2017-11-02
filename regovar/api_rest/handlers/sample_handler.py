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
# SAMPLE HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 





class SampleHandler:
    
    def build_tree(subject_id):
        from core.core import core

        currentLevelProjects = core.projects.get(None, {"subject_id": subject_id, "is_sandbox": False}, None, None, None, 1)
        result = []

        for p in currentLevelProjects:
            entry = p.to_json(["id", "name", "comment", "subject_id", "update_date", "create_date", "is_sandbox", "is_folder"])

            if p.is_folder:
                entry["children"] = ProjectHandler.build_tree(p.id)
            else:
                entry["subjects"] = [o.to_json(["id", "name", "comment", "update_date", "create_date"]) for o in p.subjects]
                entry["analyses"] = [o.to_json(["id", "name", "comment", "update_date", "create_date"]) for o in p.analyses]
                entry["analyses"] += [o.to_json(["id", "name", "comment", "update_date", "create_date"]) for o in p.jobs]


            result.append(entry)


        return result



    def tree(self, request):
        """
            Get samples as tree of samples (with subject as folders)
            Samples that are not linked to a subject are grouped into an "empty" subject
        """
        ref_id = request.match_info.get('ref_id', None)
        if ref_id is None:
            return rest_error("A valid referencial id must be provided to get samples tree")
        # TODO : check that ref_id exists in database
        # TODO : pagination
        # TODO : search parameters
        result = []
        samples = [s for s in session().query(Sample).filter_by(reference_id=ref_id).order_by(Sample.subject_id).all()]
        current_subject = {"id":-1}
        for s in samples:
            if s.subject_id != current_subject["id"]:
                if current_subject["id"] != -1: result.append(current_subject)
                current_subject = {"id": s.subject_id, "samples": []}
            
            s.init(1)
            current_subject["samples"].append(s.to_json())
        if current_subject["id"] != -1: 
            result.append(current_subject)
        return rest_success(result)
    
    
    def list(self, request):
        # Generic processing of the get query
        fields, query, order, offset, limit = process_generic_get(request.query_string, Sample.public_fields)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('depth', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Sample.count(),
            "range_max"    : RANGE_MAX,
        }
        # Return result of the query.
        samples = core.samples.get(fields, query, order, offset, limit, depth)
        return rest_success([s.to_json() for s in samples], range_data)


    def get(self, request):
        sid = request.match_info.get('sample_id', None)
        if sid is None:
            return rest_error("No valid sample id provided")
        sample = Sample.from_id(sid, 1)
        if sample is None:
            return rest_error("No sample found with id="+str(sid))
        return rest_success(sample.to_json())




    async def import_from_file(self, request):
        params = get_query_parameters(request.query_string, ["subject_id", "analysis_id"])
        file_id = request.match_info.get('file_id', None)
        ref_id = request.match_info.get('ref_id', None)
        
        
        try:
            samples = await core.samples.import_from_file(file_id, ref_id)
        except Exception as ex:
            return rest_error("Import error : enable to import samples. ".format(str(ex)))
        if samples:
            for s in samples:
                if params["subject_id"]: 
                    s.subject_id = params["subject_id"]
                else:
                    # TODO: create new empty subject and associate it to the sample
                    log("TODO : link sample {} to new empty subject".format(s.id))
                if params["analysis_id"]: 
                    AnalysisSample.new(s.id, params["analysis_id"])
            return rest_success([s.to_json() for s in samples])
        
        return rest_error("unable to import samples from file.")
    
    
    
    
    async def update(self, request):
        """
            Update a sample with provided data
        """
        sample_id = request.match_info.get('sample_id', -1)
        data = await request.json()
        try:
            sample = Sample.from_id(sample_id, 1)
            sample.load(data)
            sample.save()
        except Exception as ex:
            return rest_error("Unable to update sample data with provided informations. ".format(str(ex)))
        return rest_success(sample.to_json())
    