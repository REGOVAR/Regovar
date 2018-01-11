  #!env/python3
# coding: utf-8

from core.framework.common import *
from core.framework.postgresql import *




ANALYSIS_DEFAULT_FILTER = ["AND", []]



def analysis_init(self, loading_depth=0):
    """
        Init properties of an analysis :
            - id                : int           : the unique id of the analysis in the database
            - project_id        : int           : the id of the project that owns this analysis
            - name              : str           : the name of the analysis
            - comment           : str           : an optional comment
            - settings          : json          : parameters used to init the analysis
            - fields            : [str]         : The list of field's id to display
            - filter            : json          : The last current filter to applied
            - order             : [str]         : The list of field's id to used to order result
            - selection         : [str]         : The list of ids of selected variants
            - create_date       : datetime      : The date when the analysis have been created
            - update_date       : datetime      : The last time that the analysis have been updated
            - total_variants    : int           : The total number of variant in this analysis
            - reference_id      : int           : Refer to the id of the reference used for this analysis
            - computing_progress: json          : Used when the working table is computed to store the current progress, error, messages, ...
            - status            : enum          : The status of the analysis : 'empty', 'computing', 'ready', 'error'
            - filters_ids       : [int]         : The list of ids of filters saved for this analysis
            - samples_ids       : [int]         : The list of ids of samples used for analysis
            - files_ids         : [int]         : The list of ids of files associated to the analysis (via analysis_file table)
            - attributes        : json          : The list of attributes defined for this analysis
            - fullpath          : [json]        : The list of folder from root to the analyses [{"id":int, "name":str},...]
            - statistics        : json          : Statistics about the analysis
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - project           : Project       : The that own the analysis
            - samples           : [Sample]      : The list of samples owns by the analysis
            - filters           : [Filter]      : The list of Filter created in the analysis
            - files             : [File]        : The list of File associated to the analysis (via analysis_file table)
    """
    from core.model.project import Project
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    # Avoid recursion infinit loop
    if hasattr(self, "loading_depth") and self.loading_depth >= loading_depth:
        return
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        if not self.filter: self.filter = ANALYSIS_DEFAULT_FILTER
        self.filters_ids = self.get_filters_ids()
        self.samples_ids = AnalysisSample.get_samples_ids(self.id)
        self.attributes = self.get_attributes()
        self.files_ids = AnalysisFile.get_files_ids(self.id)
        self.panels_ids = self.get_panels_ids()
        self.fullpath = self.get_fullpath()
        
        self.project = None
        self.samples = []
        self.filters = []
        self.files = []
        self.panels = []
        if self.loading_depth > 0:
            self.project = Project.from_id(self.project_id, self.loading_depth-1)
            self.samples = AnalysisSample.get_samples(self.id, self.loading_depth-1)
            self.filters = self.get_filters(self.loading_depth-1)
            self.files = AnalysisFile.get_files(self.id, self.loading_depth-1)
            self.panels = self.get_panels()
    except Exception as ex:
        raise RegovarException("Analysis data corrupted (id={}).".format(self.id), "", ex)
            


def analysis_from_id(analysis_id, loading_depth=0):
    """
        Retrieve analysis with the provided id in the database
    """
    analysis = Session().query(Analysis).filter_by(id=analysis_id).first()
    if analysis:
        analysis.init(loading_depth)
    return analysis



def analysis_to_json(self, fields=None, loading_depth=-1):
    """
        export the analysis into json format
        - fields lazy loading
        - custom recursive depth loading (max 2)
    """
    result = {}
    if loading_depth < 0:
        loading_depth = self.loading_depth
    if fields is None:
        fields = Analysis.public_fields
    for field in fields:
        if field == "create_date" or field == "update_date":
            result.update({field: eval("self." + field + ".isoformat()")})
        elif field in ["samples", "filters", "files"]:
            if hasattr(self, field) and len(eval("self." + field)) > 0 and loading_depth > 0:
                result[field] = [o.to_json(None, loading_depth-1) for o in eval("self." + field)]
            else:
                result[field] = []
        elif field in ["project"] and loading_depth>0:
            obj = eval("self." + field)
            result[field] = obj.to_json(None, loading_depth-1) if obj else None
        else:
            try:
                result.update({field: eval("self." + field)})
            except Exception as ex:
                err("Analysis.to_json unable to evaluate the value of the field {}. {}".format(field, str(ex)))
    return result
    
    

def analysis_load(self, data):
    """
        Helper to update several paramters at the same time. Note that dynamics properties (project, samples, files, attributes)
        cannot be updated with this method. However, you can update project_id .
        To update sample you must used dedicated models object : AnalysisSample
    """
    from core.model.project import Project
    settings = False
    need_to_clean_db = False
    try:
        if "name"               in data.keys(): self.name               = data['name']
        if "project_id"         in data.keys(): self.project_id         = data['project_id']
        if "comment"            in data.keys(): self.comment            = data['comment']
        if "create_date"        in data.keys(): self.create_date        = data['create_date']
        if "update_date"        in data.keys(): self.update_date        = data['update_date']
        if "fields"             in data.keys(): self.fields             = data["fields"]
        if "filter"             in data.keys(): self.filter             = data["filter"]
        if "selection"          in data.keys(): self.selection          = data["selection"]
        if "order"              in data.keys(): self.order              = data["order"]
        if "total_variants"     in data.keys(): self.total_variants     = data["total_variants"]
        if "reference_id"       in data.keys(): self.reference_id       = data["reference_id"]
        if "computing_progress" in data.keys(): self.computing_progress = data["computing_progress"]
        if "status"             in data.keys(): self.status             = data["status"] if data["status"] else 'empty'
        if "attributes"         in data.keys(): self.attributes         = data["attributes"]
        if "statistics"         in data.keys(): self.statistics         = data["statistics"]
        
        if "files_ids" in data.keys(): 
            self.files_ids = data['files_ids']
            # Remove old
            for fid in self.files_ids:
                if fid not in data["files_ids"]:
                    AnalysisFile.delete(self.id, fid)
            # Add new samples
            for fid in data["files_ids"]:
                if fid not in self.files_ids:
                    AnalysisFile.new(self.id, sid)
            
        if "settings" in data.keys(): 
            # When settings change, need to regenerate working table
            self.settings = data["settings"]
            self.status = "empty"
            self.computing_progress = None
            need_to_clean_db = True
            

        if "samples_ids" in data.keys():
            # Remove old
            for sid in self.samples_ids:
                if sid not in data["samples_ids"]:
                    AnalysisSample.delete(self.id, sid)
            # Add new samples
            for sid in data["samples_ids"]:
                if sid not in self.samples_ids:
                    AnalysisSample.new(self.id, sid)
            # When settings change, need to regenerate working table
            self.status = "empty"
            self.computing_progress = None
            need_to_clean_db = True

            # If settings empty, init it with informations from samples
            if len(self.settings["annotations_db"]) == 0:
                settings = self.settings
                from core.model.sample import Sample
                dbuids = []
                for sid in data["samples_ids"]:
                    sample = Sample.from_id(sid)
                    if sample and sample.default_dbuid:
                        for dbuid in sample.default_dbuid:
                            if dbuid not in dbuids:
                                dbuids.append(dbuid)
                self.status = "empty"
                settings["annotations_db"] = dbuids
                self.settings = settings

        
        if need_to_clean_db:
            execute("DROP TABLE IF EXISTS wt_{0} CASCADE; DROP TABLE IF EXISTS wt_{0}_var CASCADE;".format(self.id))

        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.project = Project.from_id(self.project_id, self.loading_depth-1)
            self.samples = AnalysisSample.get_samples(self.id, self.loading_depth-1)
            self.filters = self.get_filters(self.loading_depth-1)
            self.files = AnalysisFile.get_files(self.id, self.loading_depth-1)
        self.save()

        # FIXME : why sqlalchemy don't care about json settings the first time ?
        if settings:
            self.settings = settings
            self.save()
        # END FIXME
    except Exception as ex:
        raise RegovarException('Invalid input data to load.', "", ex)
    return self



def analysis_delete(analysis_id):
    """
        Delete the Analysis with the provided id in the database
    """
    # TODO : delete linked filters, AnalysisSample, Attribute, WorkingTable
    Session().query(Analysis).filter_by(id=analysis_id).delete(synchronize_session=False)


def analysis_new():
    """
        Create a new Analysis and init/synchronise it with the database
    """
    a = Analysis()
    a.fields=[]
    a.filter=ANALYSIS_DEFAULT_FILTER
    a.selection=[]
    a.order=[]
    a.settings = {"trio": False, "annotations_db": []}
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
    filters = Session().query(Filter).filter_by(analysis_id=self.id).order_by(Filter.id).all()
    for f in filters:
        result.append(f.id)
    return result



def analysis_get_filters(self, loading_depth=0):
    """
        Return the list of filters saved in the analysis
    """
    filters = Session().query(Filter).filter_by(analysis_id=self.id).all()
    for f in filters: f.init(loading_depth)
    return filters



def analysis_get_attributes(self):
    """
        Return the list of attributes saved in the analysis
    """
    result = []
    sql = "SELECT * FROM attribute WHERE analysis_id={} ORDER BY name, sample_id".format(self.id)
    attributes = execute(sql)
    current_attribute = None
    for a in attributes:
        if current_attribute is None or current_attribute != a.name:
            current_attribute = a.name
            result.append({"name": a.name, "samples_values": {a.sample_id: {'value': a.value, 'wt_col_id': a.wt_col_id}}, "values_map" : {a.value : a.wt_col_id}})
        else:
            result[-1]["samples_values"][a.sample_id] = {'value': a.value, 'wt_col_id': a.wt_col_id}
            result[-1]["values_map"][a.value] = a.wt_col_id
    return result



def analysis_get_panels_ids(self):
    """
        Return the list of panels versions ids used for this analyses (set in settings)
    """
    return self.settings["panels"]  if "panels" in self.settings else []



def analysis_get_panels(self):
    """
        Return the list of panels versions used for this analyses (set in settings)
    """
    panels_ids = self.settings["panels"]  if "panels" in self.settings else []
    result = []
    refgene_table = "refgene_{}".format(execute("SELECT table_suffix FROM reference WHERE id={}".format(self.reference_id)).first().table_suffix)
    if len(panels_ids)>0:
        data = execute("SELECT p.name, p.id AS panel_id, pv.version, pv.id AS version_id, pv.data FROM panel_entry pv INNER JOIN panel p ON pv.panel_id=p.id WHERE pv.id IN ('{}')".format("','".join(panels_ids)))
        for panel_data in data:
            # Get panel data
            panel_result = {"name": panel_data.name, "version": panel_data.version, "panel_id": panel_data.panel_id, "version_id":panel_data.version_id, "entries": []}
            for data in panel_data.data:
                if "chr" in data:
                    panel_result["entries"].append({"chr" : data["chr"], "start": data["start"], "end": data["end"]})
                elif "id" in data:
                    gene_data = execute("SELECT chr, txrange FROM {} WHERE name2='{}'".format(refgene_table, data["label"])).first()
                    if gene_data:
                        panel_result["entries"].append({"chr" : gene_data.chr, "start": gene_data.txrange.lower, "end": gene_data.txrange.upper})
                    else:
                        war("Gene '{}' have not been retrieved in {} for the panel {}. TODO: MUST implement search from former symbols and synonyms".format(data["label"], refgene_table, panel_data.id))
        result.append(panel_result)
    return result


def analaysis_get_fullpath(self):
    """
        Return the list of project from the root to the last one where the analysis is stored
    """
    from core.model import Project
    fullpath = []
    project = Project.from_id(self.project_id)
    while project is not None:
        fullpath.insert(0,{"id": project.id, "name":project.name})
        project = None if not project.parent_id else Project.from_id(project.parent_id)
    
    return fullpath


Analysis = Base.classes.analysis
Analysis.public_fields = ["id", "name", "project_id", "settings", "samples_ids", "samples", "filters_ids", "filters", "attributes", "comment", "create_date", "update_date", "fields", "filter", "selection", "order", "total_variants", "reference_id", "files_ids", "files", "computing_progress", "status", "panels_ids", "panels", "fullpath", "statistics"]
Analysis.init = analysis_init
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
Analysis.get_panels_ids = analysis_get_panels_ids
Analysis.get_panels = analysis_get_panels
Analysis.get_fullpath = analaysis_get_fullpath






# =====================================================================================================================
# FILTER
# =====================================================================================================================
def filter_new(analysis_id, name=None, filter=None, total=0):
    f = Filter(analysis_id=analysis_id, file_id=file_id, name=name, filter=filter, total_variants=total)
    f.save()
    return f


def filter_save(self):
    generic_save(self)


Filter = Base.classes.filter
Filter.new = filter_new
Filter.save = filter_save



# =====================================================================================================================
# ANALYSIS SAMPLE
# =====================================================================================================================
AnalysisSample = Base.classes.analysis_sample


def analysissample_get_samples_ids(analysis_id):
    """
        Return the list of samples ids of an analysis
    """
    return [s.sample_id for s in Session().query(AnalysisSample).filter_by(analysis_id=analysis_id).all()]


def analysissample_get_analyses_ids(sample_id):
    """
        Return the list of analyses ids where the sample is used
    """
    return [a.analysis_id for a in Session().query(AnalysisSample).filter_by(sample_id=sample_id).all()]


def analysissample_get_samples(analysis_id, loading_depth=0):
    """
        Return the list of samples used in an analysis
    """
    from core.model.sample import Sample
    samples_ids = analysissample_get_samples_ids(analysis_id)
    result = []
    if len(samples_ids) > 0:
        samples = Session().query(Sample).filter(Sample.id.in_(samples_ids)).all()
        for s in samples:
            s.init(loading_depth)
            result.append(s)
    return result


def analysissample_get_analyses(sample_id, loading_depth=0):
    """
        Return the list of analyses that used the sample
    """
    result = []
    analyses_ids = analysissample_get_analyses_ids(sample_id)
    if len(analyses_ids) > 0:
        analyses = Session().query(Analysis).filter(Analysis.id.in_(analyses_ids)).all()
        for a in analyses:
            a.init(loading_depth)
            result.append(a)
    return result


def analysissample_new(analysis_id, sample_id, nickname=None):
    """
        Create a new sample-file association and save it in the database
    """
    sf = AnalysisSample(sample_id=sample_id, analysis_id=analysis_id, nickname=nickname)
    sf.save()
    return sf


def analysissample_delete(analysis_id, sample_id):
    """
        Delete the link between an analysis and a sample
    """
    # TODO : delete linked filters, AnalysisSample, Attribute, WorkingTable
    Session().query(AnalysisSample).filter_by(analysis_id=analysis_id, sample_id=sample_id).delete()


AnalysisSample = Base.classes.analysis_sample
AnalysisSample.get_samples_ids = analysissample_get_samples_ids
AnalysisSample.get_analyses_ids = analysissample_get_analyses_ids
AnalysisSample.get_samples = analysissample_get_samples
AnalysisSample.get_analyses = analysissample_get_analyses
AnalysisSample.save = generic_save
AnalysisSample.new = analysissample_new
AnalysisSample.delete = analysissample_delete




# =====================================================================================================================
# ANALYSIS FILE
# =====================================================================================================================
AnalysisFile = Base.classes.analysis_file


def analysisfile_get_files_ids(analysis_id):
    """
        Return the list of file ids of an analysis
    """
    return [f.file_id for f in Session().query(AnalysisFile).filter_by(analysis_id=analysis_id).all()]


def analysisfile_get_analyses_ids(file_id):
    """
        Return the list of analyses ids where the file is linked
    """
    return [a.analysis_id for a in Session().query(AnalysisFile).filter_by(file_id=file_id).all()]


def analysisfile_get_files(analysis_id, loading_depth=0):
    """
        Return the list of files used in an analysis
    """
    from core.model.file import File
    files_ids = analysisfile_get_files_ids(analysis_id)
    result = []
    if len(files_ids) > 0:
        files = Session().query(File).filter(File.id.in_(files_ids)).all()
        for f in files:
            f.init(loading_depth)
            result.append(f)
    return result


def analysisfile_get_analyses(file_id, loading_depth=0):
    """
        Return the list of analyses that have the file
    """
    result = []
    analyses_ids = analysisfile_get_analyses_ids(sample_id)
    if len(analyses_ids) > 0:
        analyses = Session().query(Analysis).filter(Analysis.id.in_(analyses_ids)).all()
        for a in analyses:
            a.init(loading_depth)
            result.append(a)
    return result


def analysisfile_new(analysis_id, file_id):
    """
        Create a new analysis-file association and save it in the database
    """
    sf = AnalysisFile(analysis_id=analysis_id, file_id=file_id)
    sf.save()
    return sf


def analysisfile_delete(analysis_id, file_id):
    """
        Delete the link between an analysis and a file
    """
    # TODO : delete linked filters, AnalysisFile, Attribute, WorkingTable
    Session().query(AnalysisFile).filter_by(analysis_id=analysis_id, file_id=file_id).delete()


AnalysisFile = Base.classes.analysis_file
AnalysisFile.get_files_ids = analysisfile_get_files_ids
AnalysisFile.get_analyses_ids = analysisfile_get_analyses_ids
AnalysisFile.get_files = analysisfile_get_files
AnalysisFile.get_analyses = analysisfile_get_analyses
AnalysisFile.save = generic_save
AnalysisFile.new = analysisfile_new
AnalysisFile.delete = analysisfile_delete



