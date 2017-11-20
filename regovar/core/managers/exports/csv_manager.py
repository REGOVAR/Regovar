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
            "output" :  ["csv", "tsv"],  # list of file extension that manage the export manager
            "description" : "Export variants into a flat file with columns separeted by comma (CSV) or tab (TSV)" # short desciption about what it does
        }




    @staticmethod
    async def export_data(analysis_id, **kargs):
        """
            Retrieve selected variant of the given analysis and export them is the requested format
        """
        from core.core import core
        
        # Check analysis
        analysis = Analysis.from_id(analysis_id)
        if not analysis:
            return {"success": False, "error": "Analysis not found"}
        
        # Check parameters 
        separator = ";"
        extension = ".csv"
        if "separator" in kargs.keys() and kargs["separator"] in [";", "\t"]:
            separator = kargs["separator"]
            extension = ".csv" if separator == ";" else ".tsv"
        with_header = True
        if "with_header" in kargs.keys():
            with_header = kargs["with_header"]
        filename = "Selection export {}.csv".format(datetime.datetime.now().date().isoformat())
        if "filename" in kargs.keys():
            filename = clean_filename(kargs["filename"])
            filename += "" if filename.endswith(extension) else extension
            
        # Write file
        data = core.analyses.get_selection(analysis_id)
        if not data or not isinstance(data, list) or len(data) == 0:
            return {"success": False, "error": "Not eble to retrieve a valid selection for this analysis."}
        
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
        return f.to_json()
                
        
        






