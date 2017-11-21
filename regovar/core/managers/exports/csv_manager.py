#!env/python3
# coding: utf-8

import ipdb
import sqlalchemy
import datetime

from core.managers.exports.abstract_export_manager import AbstractVariantExportManager
from core.framework.common import *
from core.model import *
from config import TEMP_DIR





            
class Exporter(AbstractVariantExportManager): 
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
        """
            Retrieve selected variant of the given analysis and export them is the requested format
            Return None or the File object
        """
        from core.core import core
        
        # Check analysis
        analysis = Analysis.from_id(analysis_id)
        if not analysis:
            raise RegovarException("Not ebale to find analysis with the provided id.")
        
        # Check parameters 
        separator = ";"
        if "separator" in kargs.keys() and kargs["separator"] in [";", "\t"]:
            separator = kargs["separator"]
        with_header = True
        if "with_header" in kargs.keys():
            with_header = kargs["with_header"]
        filename = "Selection export {}.csv".format(datetime.datetime.now().date().isoformat())
        if "filename" in kargs.keys():
            filename = clean_filename(kargs["filename"])
            filename += ".csv"
            
        # Write file
        data = core.analyses.get_selection(analysis_id)
        if not data or not isinstance(data, list) or len(data) == 0:
            raise RegovarException("Not able to retrieve a valid selection for this analysis.")
        
        path = os.path.join(TEMP_DIR, filename)
        fields = [f for f in data[0].keys()]
        with open(path, "w") as f:
            # write headers
            if with_header:
                f.write(separator.join(fields) + "\n")
            # write values
            for row in data:
                f.write(separator.join([str(row[f]) for f in fields]) + "\n")
            f.close()
            
        # Create file entry and link it to the analysis
        f = core.files.from_local(path, True)
        AnalysisFile.new(analysis_id, f.id)
        return f
                
        
        






