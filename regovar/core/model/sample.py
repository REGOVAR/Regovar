    #!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *













def sample_init(self, loading_depth=0):
    """
        Init properties of a sample :
            - id               : int        : the unique id of the sample in the database
            - name             : str        : the name of the sampel (name in the vcf file by default)
            - comment          : str        : a comment on the sample
            - is_mosaic        : bool       : true if data (variant) for this sample are mosaic; false otherwise
            - subject_id       : int        : the id of the subject linked to this sample
            - file_id          : int        : the id of the file (vcf) from which the sample have been extracted
            - file             : File       : File data of the source file 
            - loading_progress : float      : progress (from 0 to 1) of the import of the sample
            - update_date      : date       : The last time that the object have been updated
            - create_date      : date       : The datetime when the object have been created
            - reference_id     : int        : the reference id for this sample
            - status           : enum       : import status values can be : 'empty', 'loading', 'ready', 'error'
            - default_dbuid    : [str]      : list of annotation's databases used in the vcf from where come the sample
            - filter_description json       : description of the filter used in the vcf. Structure : { "<FilterValue>": "<Description>"}
            - analyses_id      : [int]      : the list of id of analyses that are using this sample
            - stats            : json       : stats regarding import and quality
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - subject          : Subject    : Subject data of the linked subject
            - analyses         : [Analysis] : Analysis data of linked analyses
    """
    from core.model.analysis import Analysis, AnalysisSample
    from core.model.subject import Subject
    from core.model.file import File
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth") and self.loading_depth >= loading_depth:
        return
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        self.analyses_ids = AnalysisSample.get_analyses_ids(self.id)
        self.subject = None
        self.file = File.from_id(self.file_id, 0)
        self.analyses = []
        if self.loading_depth > 0:
            self.subject = Subject.from_id(self.subject_id, self.loading_depth-1)
            self.analyses = AnalysisSample.get_analyses(self.id, self.loading_depth-1)
    except Exception as ex:
        raise RegovarException("Sample data corrupted (id={}).".format(self.id), "", ex)



def sample_from_id(sample_id, loading_depth=0):
    """
        Retrieve sample with the provided id in the database
    """
    sample = Session().query(Sample).filter_by(id=sample_id).first()
    if sample : 
        Session().refresh(sample)
        sample.init(loading_depth)
    return sample



def sample_to_json(self, fields=None, loading_depth=-1):
    """
        export the sample into json format
        - fields lazy loading
        - custom recursive depth loading (max 2)
    """
    result = {}
    if loading_depth < 0:
        loading_depth = self.loading_depth
    if fields is None:
        fields = Sample.public_fields
    for f in fields:
        if f in ["create_date", "update_date"]:
            result[f] = eval("self." + f + ".isoformat()")
        elif f in ["analyses"]:
            if hasattr(self, f) and len(eval("self." + f)) > 0 and loading_depth > 0:
                result[f] = [o.to_json(None, loading_depth-1) for o in eval("self." + f)]
            else :                           
                result[f] = []
        elif f in ["subject", "file"]:
            if  loading_depth > 0 and hasattr(self, f) and eval("self." + f):
                result[f] = eval("self." + f + ".to_json(None, loading_depth-1)")
            else:
                result[f] = None
        else:
            result.update({f: eval("self." + f)})
    return result


def sample_load(self, data):
    """
        Helper to update several paramters at the same time. Note that dynamics properties like project and template
        cannot be updated with this method. However, you can update project_id and template_id.
    """
    from core.model.analysis import Analysis, AnalysisSample
    from core.model.subject import Subject
    from core.model.file import File
    try:
        # update simple properties
        if "name" in data.keys(): self.name = check_string(data['name'])
        if "comment" in data.keys(): self.comment = check_string(data['comment'])
        if "is_mosaic" in data.keys(): self.is_mosaic = check_bool(data['is_mosaic'])
        if "default_dbuid" in data.keys(): self.default_dbuid = check_string(data['default_dbuid'])
        if "filter_description" in data.keys(): self.filter_description = data['filter_description']
        if "subject_id" in data.keys(): self.subject_id = check_int(data['subject_id'])
        if "file_id" in data.keys(): self.file_id = check_int(data['file_id'])
        if "analyses_ids" in data.keys(): self.analyses_ids = data['analyses_ids']
        if "update_date" in data.keys(): self.update_date = check_date(data['update_date'])
        if "stats" in data.keys(): self.stats = data['stats']
        
        # save modifications
        self.save()

        # reload dependencies
        if self.loading_depth > 0:
            self.subject = Subject.from_id(self.subject_id, self.loading_depth-1)
            self.file = File.from_id(self.file_id, self.loading_depth-1)
            self.analyses = AnalysisSample.get_analyses(self.id, self.loading_depth-1)
    except Exception as err:
        raise RegovarException('Invalid input data to load.', "", err)
    return self



def sample_delete(sample_id):
    """
        Delete the sample with the provided id in the database
    """
    # TODO : delete linked filters, Attribute, WorkingTable
    Session().query(Sample).filter_by(id=sample_id).delete(synchronize_session=False)


def sample_new():
    """
        Create a new sample and init/synchronise it with the database
    """
    a = Sample()
    a.save()
    a.init()
    return a


def sample_count():
    """
        Return total of Analyses entries in database
    """
    return generic_count(Sample)



Sample = Base.classes.sample
Sample.public_fields = ["id", "name", "comment", "subject_id", "file_id", "analyses_ids", "create_date", "update_date", "is_mosaic", "default_dbuid", "filter_description", "loading_progress", "reference_id", "status", "subject", "file", "analyses", "stats"]
Sample.init = sample_init
Sample.from_id = sample_from_id
Sample.to_json = sample_to_json
Sample.load = sample_load
Sample.save = generic_save
Sample.delete = sample_delete
Sample.new = sample_new
Sample.count = sample_count



