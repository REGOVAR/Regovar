#!env/python3
# coding: utf-8
import ipdb

import os
import json
import datetime
import uuid
import psycopg2
import hashlib
import asyncio
import ped_parser



from config import *
from core.framework.common import *
import core.model as Model





# =====================================================================================================================
# Samples MANAGER
# =====================================================================================================================


class SampleManager:
    def __init__(self):
        pass





    def get(self, fields=None, query:str=None, order:str=None, offset:int=None, limit:int=None, depth:int=0):
        """
            Generic method to get sample data according to provided filtering options
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {}
        if order is None:
            order = "name"
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        s = Model.Session()
        samples = s.query(Model.Sample).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for s in samples: s.init(depth)
        return samples
 
 
 
    async def import_from_file(self, file_id:int, reference_id:int, analysis_id:int=None):
        from core.managers.imports.vcf_manager import VcfManager
        # Check ref_id
        if analysis_id:
            analysis = Model.Analysis.from_id(analysis_id)
            if analysis and not reference_id:
                reference_id=analysis.reference_id
        
        # create instance of importer
        importer = VcfManager() # Only import from VCF is supported for samples
        print ("Using import manager {}. {}".format(VcfManager.metadata["name"],VcfManager.metadata["description"]))
        try:
            result = await importer.import_data(file_id, reference_id=reference_id)
        except Exception as ex:
            msg = "Error occured when caling: core.samples.import_from_file > VcfManager.import_data(file_id={}, ref_id={}).".format(file_id, reference_id)
            raise RegovarException(msg, exception=ex)   
        
        # if analysis_id set, associate it to sample
        if result and result["success"]:
            samples = [result["samples"][s] for s in result["samples"].keys()]
            
            if analysis_id:
                for s in samples:
                    Model.AnalysisSample.new(s.id, analysis_id)
                    s.init()
        if result["success"]:
            return [result["samples"][s] for s in result["samples"].keys()]
        
        return False # TODO raise error
    
    
    
    