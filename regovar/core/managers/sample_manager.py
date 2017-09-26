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





    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
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
        s = Model.session()
        samples = s.query(Model.Sample).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for s in samples: s.init(depth)
        return samples
 
 
 
    async def import_from_file(self, file_id, reference_id, analysis_id=None):
        from core.managers.imports.vcf_manager import VcfManager
        # Check ref_id
        if analysis_id:
            analysis = Model.Analysis.from_id(analysis_id)
            if analysis and not reference_id:
                reference_id=analysis.reference_id
        # Only import from VCF is supported for samples
        print ("Using import manager {}. {}".format(VcfManager.metadata["name"],VcfManager.metadata["description"]))
        result = await VcfManager.import_data(file_id, reference_id=reference_id)
        
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