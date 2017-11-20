#!env/python3
# coding: utf-8

import ipdb
import sqlalchemy
import datetime

from core.managers.reports.abstract_report_manager import AbstractReportManager
from core.framework.common import *
from core.model import *
from config import TEMP_DIR





            
class Report(AbstractReportManager): 
    metadata = {
            "name" : "Hugodims v1",
            "output" : "html",
            "description" : "DI oriented report about selected variant of the analysis."
        }




    @staticmethod
    async def generate(analysis_id, **kargs):
        """
            Retrieve selected variant of the given analysis and export them is the requested format
            Return None or the File object
        """
        from core.core import core
        
        # Check analysis
        analysis = Analysis.from_id(analysis_id)
        if not analysis:
            raise RegovarException("Not ebale to find analysis with the provided id")
        
        # Check parameters
        filename = "Hugodims report {}.html".format(datetime.datetime.now().date().isoformat())
        if "filename" in kargs.keys():
            filename = clean_filename(kargs["filename"])
            filename += "" if filename.endswith(extension) else extension
            
        # Write file
        data = core.analyses.get_selection(analysis_id)
        if not data or not isinstance(data, list) or len(data) == 0:
            raise RegovarException("Not able to retrieve a valid selection for this analysis.")
        
        path = os.path.join(TEMP_DIR, filename)
        fields = [f for f in data[0].keys()]
        with open(path, "w") as f:
            f.write("<html><h1>Hello world!</h1></html>\n")
            f.close()
            
        # Create file entry and link it to the analysis
        f = core.files.from_local(path, True)
        AnalysisFile.new(analysis_id, f.id)
        return f
                
        
        






 
