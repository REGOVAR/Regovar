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
 




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# ANALYSIS HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class AnalysisHandler:




    def list(self, request):
        """
            Return all data about the analysis with the provided id (analysis metadata: name, settings, template data, samples used, filters, ... )
        """
        # Generic processing of the get query
        fields, query, order, offset, limit = process_generic_get(request.query_string, Analysis.public_fields)
        depth = int(MultiDict(parse_qsl(request.query_string)).get('depth', 0))
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Analysis.count(),
            "range_max"    : RANGE_MAX,
        }
        # Return result of the query.
        analyses = core.analyses.get(fields, query, order, offset, limit, depth)
        return rest_success([a.to_json() for a in analyses], range_data)



    def get(self, request):
        """
            Return all data about the analysis with the provided id (analysis metadata: name, settings, template data, samples used, filters, ... )
        """
        analysis_id = request.match_info.get('analysis_id', -1)
        analysis = Analysis.from_id(analysis_id, 2)
        if not analysis:
            return rest_error("Unable to find the analysis with id=" + str(analysis_id))
        return rest_success(analysis.to_json())



    async def new(self, request):
        """
            Creae 
        """
        # 1- Retrieve data from request
        data = await request.json()
        try:
            
            project_id = data["project_id"]
            name = data["name"]
            ref_id = data["reference_id"]
            samples = data["samples_ids"] if "samples_ids" in data.keys() else []
            settings = data["settings"] if "settings" in data.keys() else None
            template_id = data["template_id"] if "template_id" in data.keys() else None
        except Exception as ex:
            return rest_error("Unable to create new analysis. Provided data missing or corrupted. " + str(ex))
        # Create the analysis 
        analysis = core.analyses.create(name, project_id, ref_id, template_id)
        core.analyses.update(analysis.id, data)
        if not analysis:
            return rest_error("Unable to create an analsis with provided information.")
        return rest_success(analysis.to_json())




    async def update(self, request):
        # 1- Retrieve data from request
        analysis_id = request.match_info.get('analysis_id', -1)
        data = await request.json()
        try:
            result = core.analyses.update(analysis_id, json.loads(data))
        except Exception as err:
            return rest_error("Error occured when trying to save settings for the analysis with id=" + str(analysis_id) + ". " + str(err))
        return rest_success(result.to_json()) 

        

    async def filtering(self, request):
        # 1- Retrieve data from request
        data = await request.json()
        if isinstance(data, str): data = json.loads(data)
        analysis_id = request.match_info.get('analysis_id', -1)
        variant_id = request.match_info.get('variant_id', None)
        
        filter_json = data["filter"] if "filter" in data else None
        if isinstance(filter_json, str): filter_json = json.loads(filter_json)
        
        fields = data["fields"] if "fields" in data else None
        if isinstance(fields, str): fields = json.loads(fields)
        
        limit = data["limit"] if "limit" in data else 100
        offset = data["offset"] if "offset" in data else 0
        order = data["order"] if "order" in data else None
        if isinstance(order, str): order = json.loads(order)

        # 2- Check parameters
        if limit<0 or limit > RANGE_MAX: limit = 100
        if offset<0: offset = 0
        
        # 3- Execute filtering request
        try:
            result = await core.filters.request(int(analysis_id), filter_json, fields, order, variant_id, int(limit), int(offset))
        except Exception as err:
            return rest_error("Filtering error: " + str(err))
        return rest_success(result)





    def get_filters(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)
        filters = core.analyses.get_filters(analysis_id)
        return rest_success([f.to_json() for f in filters])


    async def create_update_filter(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)
        filter_id = request.match_info.get('filter_id', None)
        analysis = Analysis.from_id(analysis_id)
        data = await request.json()
        try:
            data.update({"analysis_id": analysis_id })
            result = await core.analyses.create_update_filter(filter_id, data)
            return rest_success(result.to_json())
        except Exception as ex:
            return rest_error("Unable to create or update the filter with provided data. " + str(ex))



    def delete_filter(self, request):
        filter_id = request.match_info.get('filter_id', -1)
        # Remove column if exists in the analysis working table
        filter = Filter.from_id(filter_id)
        if filter:
            analysis = Analysis.from_id(filter.analysis_id)
            if analysis and analysis.status == "ready":
                execute("ALTER TABLE wt_{} DROP COLUMN IF EXISTS filter_{} CASCADE;".format(analysis.id, filter_id))
            # delete filter entry in the database
        Filter.delete(filter_id)
        
        return rest_success()



    def clear_temps_data(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)
        try:
            result = core.analyses.clear_temps_data(analysis_id)
            return rest_success()
        except Exception as ex:
            return rest_error("Unable to clear temporary data for analysis {}. {}".format(analysis_id, ex))



    async def get_selection(self, request):
        data = await request.json()
        analysis_id = request.match_info.get('analysis_id', -1)

        try:
            result = core.analyses.get_selection(analysis_id, data)
        except Exception as err:
            return rest_error("AnalysisHandler.get_selection error: " + str(err))
        return rest_success(result)


    #async def load_ped(self, request):
        #ped = await request.content.read()
        #analysis_id = request.match_info.get('analysis_id', -1)
        ## write ped file in temporary cache directory
        #file_path = os.path.join(DOWNLOAD_DIR, "tpm_{}.ped".format(analysis_id))
        #with open(file_path, "w") as f:
            #f.write(ped)
        ## update model
        #try:
            #core.analyses.load_ped(file_path)
        #except Exception as err:
            #os.remove(file_path)
            #return rest_error("Error occured ! Wrong Ped file: " + str(err))
        #os.remove(file_path)
        #return rest_success(result)
        
    async def load_file(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)
        file_id = request.match_info.get('file_id', -1)
        try:
            await core.analyses.load_file(analysis_id, file_id)
        except Exception as ex:
            return rest_error("Error occured ! Wrong file: " + str(ex))
        return rest_success()



    async def get_report(self, request):
        data = await request.json()
        analysis_id = request.match_info.get('analysis_id', -1)
        report_id = request.match_info.get('report_id', -1)

        try:
            cache_path = core.analyses.report(analysis_id, report_id, data)
        except Exception as err:
            return rest_error("AnalysisHandler.get_report error: " + str(err))

        # create url to access to the report
        url = '{0}/cache{1}'.format(HOST_P, cache_path[len(CACHE_DIR):])
        return rest_success({'url': url})



    async def get_export(self, request):
        data = await request.json()
        analysis_id = request.match_info.get('analysis_id', -1)
        export_id = request.match_info.get('export_id', -1)

        try:
            result = core.analyses.export(analysis_id, export_id, data)
        except Exception as err:
            return rest_error("AnalysisHandler.get_export error: " + str(err))
        return rest_success({"url": "http://your_export."+str(export_id)})

