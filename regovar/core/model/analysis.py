#!env/python3
# coding: utf-8
import os
import json

from core.framework.common import *
from core.framework.postgresql import *




ANALYSIS_DEFAULT_FILTER = '["AND", []]'




def analysis_init(self, loading_depth=0):
    """
        If loading_depth is > 0, children objects will be loaded. Max depth level is 2.
        Children objects of a analysis are :
            - filter_ids : the list of ids of filters saved for the analysis
            - sample_ids : the list of ids of samples used for the analysis
            
            - template   : set with a Template object if the analysis has been created from a template. 
            - project    : the project that own the analysis
            - samples    : the list of samples used for the analysis
            - attributes : the list of attributes used for the analysis
            - filters    : the list of saved filters
            
        If loading_depth == 0, children objects are not loaded
    """
    from core.model.attribute import Attribute
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    if not self.filter: self.filter = ANALYSIS_DEFAULT_FILTER
    self.filters_ids = self.get_filters_ids()
    self.samples_ids = AnalysisSample.get_samples_ids(self.id)
    self.attributes = Attribute.get_attributes(self.id)
    self.load_depth(loading_depth)
            

def analysis_load_depth(self, loading_depth):
    from core.model.project import Project
    from core.model.template import Template
    self.project = None
    self.template = None
    self.samples = []
    self.filters = []
    if loading_depth > 0:
        try:
            self.project = Project.from_id(self.project_id, self.loading_depth-1)
            self.template = Template.get_jobs(self.template_id, self.loading_depth-1)
            self.samples = AnalysisSample.get_samples(self.id, self.loading_depth-1)
            self.filters = self.get_filters(self.loading_depth-1)
        except Exception as ex:
            raise RegovarException("Analysis data corrupted (id={}).".format(self.id), "", ex)



def analysis_from_id(analysis_id, loading_depth=0):
    """
        Retrieve analysis with the provided id in the database
    """
    analysis = session().query(Analysis).filter_by(id=analysis_id).first()
    if analysis:
        analysis.init(loading_depth)
    return analysis



def analysis_to_json(self, fields=None):
    """
        export the analysis into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Analysis.public_fields
    for f in fields:
        if f == "create_date" or f == "update_date":
            result.update({f: eval("self." + f + ".ctime()")})
        elif f in ["fields", "filter", "selection"] :
            try:
                result.update({f: json.loads(eval("self." + f))})
            except Exception as ex:
                err("Analysis.to_json unable to load json for the field {}. {}".format(f, str(ex)))
        elif f in ["samples", "filters", "attributes"]:
            result[f] = [o.to_json() for o in eval("self." + f)]
        else:
            result.update({f: eval("self." + f)})
    return result


def analysis_load(self, data):
    """
        Helper to update several paramters at the same time. Note that dynamics properties (project, template, samples, samples_ids, attributes)
        cannot be updated with this method. However, you can update project_id and template_id.
        To update sample and Attributes you must used dedicated models object : AnalysisSample and Attribute
    """
    try:
        if "name"              in data.keys(): self.name              = data['name']
        if "owner_id"          in data.keys(): self.owner_id          = data['owner_id']
        if "project_id"        in data.keys(): self.project_id        = data['project_id']
        if "template_id"       in data.keys(): self.template_id       = data['template_id']
        if "comment"           in data.keys(): self.comment           = data['comment']
        if "create_date"       in data.keys(): self.create_date       = data['create_date']
        if "update_date"       in data.keys(): self.update_date       = data['update_date']
        if "fields"            in data.keys(): self.fields            = json.dumps(data["fields"]) if isinstance(data, list) else str(data["fields"])
        if "filter"            in data.keys(): self.filter            = json.dumps(data["filter"]) if isinstance(data, dict) else str(data["filter"])
        if "selection"         in data.keys(): self.selection         = json.dumps(data["selection"]) if isinstance(data, list) else str(data["selection"])
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
    a.fields='[]'
    a.filter='[]'
    a.selection='[]'
    a.save()
    a.init()
    return a


def analysis_count():
    """
        Return total of Analyses entries in database
    """
    return generic_count(Analysis)



def analysis_get_filters_ids(self):
    """
        Return the list of filters saved for the analysis
    """
    result = []
    filters = session().query(Filter).filter_by(analysis_id=self.id).all()
    for f in filters:
        result.append(f.id)
    return result

def analysis_get_filters(self, loading_depth=0):
    """
        Return the list of filters saved in the analysis
    """
    return session().query(Filter).filter_by(analysis_id=self.id).all()


def analysis_get_attributes_ids(self):
    """
        Return the list of attributes defined for the analysis
    """
    result = []
    attributes = session().query(Attribute).filter_by(analysis_id=self.id).all()
    for a in attributes:
        result.append(a.id)
    return result


def analysis_get_attributes(self, loading_depth=0):
    """
        Return the list of filters saved in the analysis
    """
    result = []
    attributes = session().query(Attribute).filter_by(analysis_id=self.id).order_by("name, sample_id").all()
    current_attribute = None
    for a in attributes:
        if current_attribute is None or current_attribute != a.name:
            current_attribute = a.name
            result.append({"name": a.name, "samples_value": {a.sample_id: a.value}})
        else:
            result[-1]["samples_value"][a.sample_id] = a.value


Analysis = Base.classes.analysis
Analysis.public_fields = ["id", "name", "owner_id", "project_id", "template_id", "samples_ids", "samples", "filters_ids", "filters", "attributes", "comment", "create_date", "update_date", "fields", "filter", "selection", "total_variants", "reference_id"]
Analysis.init = analysis_init
Analysis.load_depth = analysis_load_depth
Analysis.from_id = analysis_from_id
Analysis.to_json = analysis_to_json
Analysis.load = analysis_load
Analysis.save = generic_save
Analysis.delete = analysis_delete
Analysis.new = analysis_new
Analysis.count = analysis_count
Analysis.get_filters_ids = analysis_get_filters_ids
Analysis.get_filters = analysis_get_filters
Analysis.get_attributes = analysis_get_attributes



# =====================================================================================================================
# FILTER
# =====================================================================================================================

Filter = Base.classes.filter



# =====================================================================================================================
# ANALYSIS SAMPLE
# =====================================================================================================================
AnalysisSample = Base.classes.analysis_sample


def analysissample_get_samples_ids(analysis_id):
    """
        Return the list of samples ids of an analysis
    """
    return [s.sample_id for s in session().query(AnalysisSample).filter_by(analysis_id=analysis_id).all()]


def analysissample_get_analyses_ids(sample_id):
    """
        Return the list of analyses ids where the sample is used
    """
    return [a.analysis_id for a in session().query(AnalysisSample).filter_by(sample_id=sample_id).all()]


def analysissample_get_samples(analysis_id, loading_depth=0):
    """
        Return the list of samples used in an analysis
    """
    samples_ids = analysissample_get_samples_ids(analysis_id)
    if len(samples_ids) > 0:
        samples = session().query(Sample).filter(Sample.id.in_(samples_ids)).all()
    for s in samples:
        s.init(loading_depth)
        result.append(s)
    return result


def analysissample_get_analyses(sample_id, loading_depth=0):
    """
        Return the list of analyses that used the sample
    """
    analyses_ids = analysissample_get_analyses_ids(sample_id)
    if len(analyses_ids) > 0:
        analyses = session().query(Analysis).filter(Analysis.id.in_(analyses_ids)).all()
    for a in analyses:
        a.init(loading_depth)
        result.append(a)
    return result


def analysissample_new(sample_id, analysis_id, nickname=None):
    """
        Create a new sample-file association and save it in the database
    """
    sf = AnalysisSample(sample_id=sample_id, analysis_id=analysis_id, nickname=nickname)
    sf.save()
    return sf


AnalysisSample = Base.classes.analysis_sample
AnalysisSample.get_samples_ids = analysissample_get_samples_ids
AnalysisSample.get_analyses_ids = analysissample_get_analyses_ids
AnalysisSample.get_samples = analysissample_get_samples
AnalysisSample.get_analyses = analysissample_get_analyses
AnalysisSample.save = generic_save
AnalysisSample.new = analysissample_new




