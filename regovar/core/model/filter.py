#!env/python3
# coding: utf-8
import os
import json

from core.framework.common import *
from core.framework.postgresql import *



def filter_init(self, loading_depth=0):
    """
        Init properties of a filter :
            - id                : int    : the unique id of the filter in the database
            - analysis_id       : int    : the id of the analysis that owns this analysis
            - name              : str    : the name of the filter
            - description       : str    : an optional description
            - filter            : json   : the json source of the filter
            - total_variants    : int    : count of distinct variants filtered
            - total_results     : int    : count of total result (variants+trx) filtered
            - progress          : float  : progress of the saving (as we need to update wt of the analysis, it may take some time)
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - analysis          : Analysis         : The list of Job owns by the project

    """
    from core.model.analysis import Analysis, AnalysisSample
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    if loading_depth > 0:
        try:
            self.analysis = Analysis.from_id(self.analysis_id, self.loading_depth-1)
        except Exception as ex:
            raise RegovarException("Filter data corrupted (id={}).".format(self.id), "", ex)




def filter_from_id(filter_id, loading_depth=0):
    """
        Retrieve Filter with the provided id in the database
    """
    filter = session().query(Filter).filter_by(id=filter_id).first()
    if filter : filter.init(loading_depth)
    return filter

    return __db_session.query(Filter).filter_by(id=filter_id).first()



def filter_to_json(self, fields=None):
    """
        export the filter into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Filter.public_fields
    for f in fields:
        result.update({f: eval("self." + f)})
    return result



def filter_load(self, data):
    """
        Helper to update several paramters at the same time. Note that dynamics properties like project and analysis
        cannot be updated with this method. However, you can update analysis_id which will force the reloading of 
        the dynamic property analysis.
    """
    try:
        if "name"        in data.keys(): self.name        = data['name']
        if "analysis_id" in data.keys(): self.analysis_id = data['analysis_id']
        if "filter"      in data.keys(): self.filter      = data['filter']
        if "description" in data.keys(): self.description = data['description']
        if "total_variants" in data.keys(): self.total_variants = data['total_variants']
        if "total_results" in data.keys(): self.total_results = data['total_results']
        if "progress" in data.keys(): self.progress = data['progress']
        self.save()
        
    except Exception as err:
        raise RegovarException('Invalid input data to load.', "", err)
    return self



def filter_delete(filter_id):
    """
        Delete the filter with the provided id in the database
    """
    session().query(Filter).filter_by(id=filter_id).delete()
    session().commit()
    



def filter_new():
    """
        Create a new filter and init/synchronise it with the database
    """
    f = Filter()
    f.save()
    f.init()
    return f







    




Filter = Base.classes.filter
Filter.public_fields = ["id", "analysis_id", "name", "filter", "description", "total_variants", "total_results", "progress"]
Filter.init = filter_init
Filter.from_id = filter_from_id
Filter.to_json = filter_to_json
Filter.load = filter_load
Filter.new = filter_new
Filter.delete = filter_delete
Filter.save = generic_save




