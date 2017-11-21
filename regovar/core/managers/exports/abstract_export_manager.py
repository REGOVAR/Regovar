#!env/python3
# coding: utf-8
import ipdb

from core.framework.common import log, war, err




class AbstractVariantExportManager():
    # Description of the export script.
    metadata = {
        "name" : "CSV", # name of the import manager
        "description" : "Export variants into a flat file with columns separeted by comma, smicolon or tab", # short desciption about what it does
        "parameters": [
            {"separator": {
                "name": "Separator",
                "desc": "The character used to separate the different values by columns.",
                "type": "enum",
                "enum": ["Semicolon (;)", "Comma (,)", "Tab (\\t)"],
                "default": 0,
                "required": False
            }},
            {"with_header": {
                "name": "Header",
                "desc": "Check if you want columns names as first line of the file.",
                "type": "bool",
                "default": True,
                "required": False
            }},
            {"filename": {
                "name": "Filename",
                "desc": "You can specify a filename. Otherwise, a name will be generated (\"Selection export YYYY-MM-DD.csv\")",
                "type": "string",
                "default": "",
                "required": False
            }}
        ]
    }

    @staticmethod
    async def export_data(analysis_id, **kargs):
        raise NotImplementedError("The abstract method \"export_data\" of AbstractVariantExportManager must be implemented.")






        
        