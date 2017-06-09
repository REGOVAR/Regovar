#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *




def analysis_init(self, loading_depth=0):
    """
        If loading_depth is > 0, children objects will be loaded. Max depth level is 2.
        Children objects of a analysis are :
            - template : set with a Template object if the analysis has been created from a template. 
            - project  : the project that own the analysis
        If loading_depth == 0, children objects are not loaded
    """
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    self.load_depth(loading_depth)
            

def analysis_load_depth(self, loading_depth):
    from core.model.project import Project
    from core.model.template import Template
    if loading_depth > 0:
        try:
            self.project = None
            self.template = None
            self.project = Project.from_id(self.project_id, self.loading_depth-1)
            self.template = Template.get_jobs(self.template_id, self.loading_depth-1)
        except Exception as ex:
            raise RegovarException("Analysis data corrupted (id={}).".format(self.id), "", ex)



def analysis_from_id(analysis_id):
    """
        Retrieve analysis with the provided id in the database
    """
    return session().query(Analysis).filter_by(id=analysis_id).first()



def analysis_to_json(self, fields=None):
    """
        export the analysis into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Analysis.public_fields
    for f in fields:
        if f == "creation_date" or f == "update_date":
            result.update({f: eval("self." + f + ".ctime()")})
        if f == "settings" :
            result.update({f: json.loads(self.settings)})
        else:
            result.update({f: eval("self." + f)})
    return result


def analysis_load(self, data):
    """
        Helper to update several paramters at the same time. Note that dynamics properties like project and template
        cannot be updated with this method. However, you can update project_id and template_id.
    """
    try:
        if "name"              in data.keys(): self.name              = data['name']
        if "owner_id"          in data.keys(): self.owner_id          = data['owner_id']
        if "project_id"        in data.keys(): self.project_id        = data['project_id']
        if "template_id"       in data.keys(): self.template_id       = data['template_id']
        if "comment"           in data.keys(): self.comment           = data['comment']
        if "creation_date"     in data.keys(): self.creation_date     = data['creation_date']
        if "update_date"       in data.keys(): self.update_date       = data['update_date']
        if "settings"          in data.keys(): self.settings          = json.dumps(data["settings"]) if isinstance(data, dict) else str(data["settings"])
        if "total_variants"    in data.keys(): self.total_variants    = data["total_variants"]
        if "reference_id"      in data.keys(): self.reference_id      = data["reference_id"]
        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.load_depth(self.loading_depth)
        self.save()
    except Exception as err:
        raise RegovarException('Invalid input data to load.', "", err)
    return self



def analysis_delete(analysis_id):
    """
        Delete the Analysis with the provided id in the database
    """
    # TODO : delete linked filters, AnalysisSample, Attribute, WorkingTable
    session().query(Analysis).filter_by(id=analysis_id).delete(synchronize_session=False)


def analysis_new():
    """
        Create a new Analysis and init/synchronise it with the database
    """
    a = Analysis()
    a.save()
    a.init()
    return a


def analysis_count():
    """
        Return total of Analyses entries in database
    """
    return generic_count(Analysis)



Analysis = Base.classes.analysis
Analysis.public_fields = ["id", "name", "owner_id", "project_id", "template_id", "comment", "creation_date", "update_date", "settings", "total_variants", "reference_id"]
Analysis.init = analysis_init
Analysis.load_depth = analysis_load_depth
Analysis.from_id = analysis_from_id
Analysis.to_json = analysis_to_json
Analysis.load = analysis_load
Analysis.save = generic_save
Analysis.delete = analysis_delete
Analysis.new = analysis_new
Analysis.count = analysis_count






# =====================================================================================================================
# ANALYSIS SAMPLE
# =====================================================================================================================
AnalysisSample = Base.classes.analysis_sample