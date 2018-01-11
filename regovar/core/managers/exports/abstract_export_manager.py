#!env/python3
# coding: utf-8
import ipdb

from core.framework.common import log, war, err




class AbstractVariantExportManager():
    # Description of the export script.
    metadata = {
        "key":  "csv",  # internal unique id use
        "name" : "CSV", # name of the import manager
        "description" : "Export variants into a flat file with columns separeted by comma, smicolon or tab", # short desciption about what it does
        "parameters": [
            {
                "key" : "separator",
                "name": "Separator",
                "description": "The character used to separate the different values by columns.",
                "type": "enum",
                "enum": ["Semicolon (;)", "Comma (,)", "Tab (\\t)"],
                "default": 0,
                "required": False
            },
            {
                "key": "with_header",
                "name": "Header",
                "description": "Check if you want columns names as first line of the file.",
                "type": "bool",
                "default": True,
                "required": False
            },
            {
                "key": "filename",
                "name": "Filename",
                "description": "You can specify a filename. Otherwise, a name will be generated (\"Selection export YYYY-MM-DD.csv\")",
                "type": "string",
                "default": "",
                "required": False
            }
        ]
    }

    @staticmethod
    async def export_data(analysis_id, parameters):
        raise NotImplementedError("The abstract method \"export_data\" of AbstractVariantExportManager must be implemented.")






        
        