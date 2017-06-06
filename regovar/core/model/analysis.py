#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *




# =====================================================================================================================
# ANALYSIS
# =====================================================================================================================

def analysis_from_id(analysis_id):
    """
        Retrieve File with the provided id in the database
    """
    return session().query(Analysis).filter_by(id=analysis_id).first()


def analysis_to_json(self, fields=None):
    """
        export the file into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Analysis.public_fields
    for f in fields:
        if f == "creation_date" or f == "update_date":
            result.update({f: eval("self." + f + ".ctime()")})
        else:
            result.update({f: eval("self." + f)})
    return result


Analysis = Base.classes.analysis
Analysis.public_fields = ["id", "name", "template_id", "creation_date", "update_date", "settings"]
Analysis.from_id = analysis_from_id
Analysis.to_json = analysis_to_json



# =====================================================================================================================
# ANALYSIS SAMPLE
# =====================================================================================================================
AnalysisSample = Base.classes.analysis_sample