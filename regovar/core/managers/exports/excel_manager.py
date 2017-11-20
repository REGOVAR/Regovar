#!env/python3
# coding: utf-8

import ipdb
import sqlalchemy

from core.managers.exports.abstract_export_manager import AbstractVariantExportManager
from core.framework.common import *





            
class Exporter(AbstractVariantExportManager): 
    metadata = {
            "name" : "Excel", # name of the import manager
            "output" :  ["xls", "xlsx"],
            "description" : "Export variants into an excel file"
        }




    @staticmethod
    async def export_data(analysis_id, **kargs):
        """
            Retrieve selected variant of the given analysis and export them is the requested format
        """
        from core.core import core
        
               
        
        return {"success": False, "error": "Not implemented :P"}






