#!env/python3
# coding: utf-8

import ipdb
import sqlalchemy

from core.managers.exports.abstract_export_manager import AbstractVariantExportManager
from core.framework.common import *





            
class Exporter(AbstractVariantExportManager): 
    # Description of the export script.
    metadata = {
        "key":  "excel",  # internal unique id use
        "name" : "Excel", # name of the import manager
        "description" : "Export variants into an excel file", # short desciption about what it does
        "parameters": [
            {
                "key": "with_header",
                "name": "Header",
                "description": "Check if you want columns names in the first row.",
                "type": "bool",
                "default": True,
                "required": False
            },
            {
                "key": "filename",
                "name": "Filename",
                "description": "You can specify a filename. Otherwise, a name will be generated (\"Selection export YYYY-MM-DD.xlsx\")",
                "type": "string",
                "default": "",
                "required": False
            }
        ]
    }



    @staticmethod
    async def export_data(analysis_id, parameters):
        """
            Retrieve selected variant of the given analysis and export them is the requested format
        """
        from core.core import core
        
               
        
        return {"success": False, "error": "Not implemented :P"}






