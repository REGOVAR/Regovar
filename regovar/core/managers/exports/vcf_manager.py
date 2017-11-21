#!env/python3
# coding: utf-8

import ipdb
import sqlalchemy

from core.managers.exports.abstract_export_manager import AbstractVariantExportManager
from core.framework.common import *





            
class Exporter(AbstractVariantExportManager): 
    # Description of the export script.
    metadata = {
        "name" : "VCF", # name of the import manager
        "description" : "Export variants into a vcf file", # short desciption about what it does
        "parameters": [
            {"filename": {
                "name": "Filename",
                "desc": "You can specify a filename. Otherwise, a name will be generated (\"Selection export YYYY-MM-DD.vcf\")",
                "type": "string",
                "default": "",
                "required": False
            }}
        ]
    }



    @staticmethod
    async def export_data(analysis_id, **kargs):
        """
            Retrieve selected variant of the given analysis and export them is the requested format
        """
        from core.core import core
        
               
        
        return {"success": False, "error": "Not implemented :P"}






