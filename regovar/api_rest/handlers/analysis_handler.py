#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp
import aiohttp_jinja2
import datetime
import time


from aiohttp import web
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
            List all analyses
        """
        return rest_success(core.analyses.list())



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
            Create new analysis
        """
        data = await request.json()
        if isinstance(data, str) : data = json.loads(data)
        
        try:
            project_id = data["project_id"]
            name = data["name"]
            ref_id = data["reference_id"]
            template_id = data["template_id"] if "template_id" in data.keys() else None
        except Exception as ex:
            return rest_error("Unable to create new analysis. Provided data missing or corrupted. " + str(ex))
        analysis = core.analyses.create(name, project_id, ref_id, template_id)
        core.analyses.update(analysis.id, data)
        if not analysis:
            return rest_error("Unable to create an analsis with provided information.")
        return rest_success(analysis.to_json())


    def delete(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)
        try:
            result = core.analyses.delete(analysis_id)
        except Exception as ex:
            return rest_error("Error occured when trying to deleting the analysis with id=" + str(analysis_id), exception=ex)
        return rest_success(result) 


    async def update(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)
        data = await request.json()
        if isinstance(data, str) : data = json.loads(data)
        
        try:
            result = core.analyses.update(analysis_id, data)
        except Exception as ex:
            return rest_error("Error occured when trying to save settings for the analysis with id=" + str(analysis_id), exception=ex)
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
        
        limit = data["limit"] if "limit" in data else RANGE_DEFAULT
        offset = data["offset"] if "offset" in data else 0
        order = data["order"] if "order" in data else None
        if isinstance(order, str): order = json.loads(order)

        # 2- Check parameters
        if limit<0 or limit > RANGE_MAX: limit = RANGE_DEFAULT
        if offset<0: offset = 0
        
        # 3- Execute filtering request
        try:
            result = await core.filters.request(int(analysis_id), filter_json, fields, order, variant_id, int(limit), int(offset))
        except Exception as ex:
            return rest_error("Filtering error", exception=ex)
        return rest_success(result)
    
    
    async def select(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)
        variant_id = request.match_info.get('variant_id', None)
        if not core.analyses.update_selection(analysis_id, True, [variant_id]):
            return rest_error("Unable to select variant.")
        return rest_success()
    
    
    
    async def unselect(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)
        variant_id = request.match_info.get('variant_id', None)
        if not core.analyses.update_selection(analysis_id, False, [variant_id]):
            return rest_error("Unable to unselect.")
        return rest_success()




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
            return rest_error("Unable to create or update the filter with provided data.", exception=ex)



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
        # force analysis to reload it's filter data
        analysis.filters_ids = analysis.get_filters_ids()
        analysis.filters = analysis.get_filters(0)
        
        return rest_success()



    def clear_temps_data(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)
        try:
            result = core.analyses.clear_temps_data(analysis_id)
            return rest_success()
        except Exception as ex:
            return rest_error("Unable to clear temporary data for analysis {}. {}".format(analysis_id, ex), exception=ex)



    def get_selection(self, request):
        analysis_id = request.match_info.get('analysis_id', -1)

        try:
            result = core.analyses.get_selection(analysis_id)
        except Exception as ex:
            return rest_error("AnalysisHandler.get_selection error", exception=ex)
        return rest_success(result)



    async def get_export(self, request):
        """
            Export selection of the requested analysis in the requested format
        """
        # Check query parameter
        data = await request.json()
        analysis_id = request.match_info.get('analysis_id', -1)
        exporter_name = request.match_info.get('exporter_name', None)
        if exporter_name not in core.exporters.keys():
            return rest_error("Exporter {} doesn't exists.".format(exporter_name))
        # export data
        try:
            export_file = await core.exporters[exporter_name]["mod"].export_data(analysis_id, **data)
        except Exception as ex:
            return rest_error("AnalysisHandler.get_export error: ", exception=ex)
        return rest_success(export_file.to_json())



    async def get_report(self, request):
        """
            Generate report for the selection of the requested analysis with the requested report generator
        """
        data = await request.json()
        analysis_id = request.match_info.get('analysis_id', -1)
        report_name = request.match_info.get('report_name', None)
        if report_name not in core.reporters.keys():
            return rest_error("Report generator {} doesn't exists.".format(report_name))
        # export data
        try:
            report_file = await core.reporters[report_name]["mod"].generate(analysis_id, **data)
        except Exception as ex:
            return rest_error("AnalysisHandler.get_report error: ", exception=ex)
        return rest_success(report_file.to_json())
    
        
        
        
        
        

