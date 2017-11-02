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
            - loading_progress : float      : progress (from 0 to 1) of the import of the sample
            - reference_id     : int        : the reference id for this sample
            - status           : enum       : import status values can be : 'empty', 'loading', 'ready', 'error'
            - default_dbuid    : [str]      : list of annotation's databases used in the vcf from where come the sample
            - filter_description json       : description of the filter used in the vcf. Structure : { "<FilterValue>": "<Description>"}
            - analyses_id      : [int]      : the list of id of analyses that are using this sample
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - subject          : Subject    : Subject data of the linked subject
            - file             : File       : File data of the source file 
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
        self.file = None
        self.analyses = []
        if loading_depth > 0:
            self.subject = Subject.from_id(self.subject_id, self.loading_depth-1)
            self.file = File.from_id(self.file_id, self.loading_depth-1)
            self.analyses = AnalysisSample.get_analyses(self.id, self.loading_depth-1)
    except Exception as ex:
        raise RegovarException("Sample data corrupted (id={}).".format(self.id), "", ex)



def sample_from_id(sample_id, loading_depth=0):
    """
        Retrieve sample with the provided id in the database
    """
    sample = session().query(Sample).filter_by(id=sample_id).first()
    if sample : sample.init(loading_depth)
    return sample



def sample_to_json(self, fields=None):
    """
        export the sample into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Sample.public_fields
    for f in fields:
        
        if f in ["analyses"] and self.loading_depth>0:
            result[f] = [o.to_json() for o in eval("self." + f)]
        elif f in ["subject", "file"] and self.loading_depth>0:
            if eval("self." + f) :
                result[f] = eval("self." + f + ".to_json()")
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
        if "name"               in data.keys(): self.name               = data['name']
        if "comment"            in data.keys(): self.comment            = data['comment']
        if "is_mosaic"          in data.keys(): self.is_mosaic          = data['is_mosaic']
        if "default_dbuid"      in data.keys(): self.default_dbuid      = data['default_dbuid']
        if "filter_description" in data.keys(): self.filter_description = data['filter_description']
        if "subject_id"         in data.keys(): self.subject_id         = data['subject_id'] 
        if "file_id"            in data.keys(): self.file_id            = data['file_id']
        if "analyses_ids"       in data.keys(): self.analyses_ids       = data['analyses_ids']
        
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
    session().query(Sample).filter_by(id=sample_id).delete(synchronize_session=False)


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
Sample.public_fields = ["id", "name", "comment", "subject_id", "file_id", "analyses_ids", "is_mosaic", "default_dbuid", "filter_description", "loading_progress", "reference_id", "status", "subject", "file", "analyses"]
Sample.init = sample_init
Sample.from_id = sample_from_id
Sample.to_json = sample_to_json
Sample.load = sample_load
Sample.save = generic_save
Sample.delete = sample_delete
Sample.new = sample_new
Sample.count = sample_count





# =====================================================================================================================
# SAMPLEFILE associations
# =====================================================================================================================
#def samplefile_get_files_ids(sample_id):
    #"""
        #Return the list of files ids of the sample
    #"""
    #result = []
    #files = session().query(SampleFile).filter_by(sample_id=sample_id).all()
    #for f in files:
        #result.append(f.file_id)
    #return result


#def samplefile_get_files(sample_id, loading_depth=0):
    #"""
        #Return the list of input's files of the job
    #"""
    #files_ids = samplefile_get_files_ids(sample_id)
    #if len(files) > 0:
        #files = session().query(File).filter(File.id.in_(files_ids)).all()
    #for f in files:
        #f.init(loading_depth)
        #result.append(f)
    #return result


#def samplefile_new(sample_id, file_id):
    #"""
        #Create a new sample-file association and save it in the database
    #"""
    #sf = SampleFile(sample_id=sample_id, file_id=file_id)
    #sf.save()
    #return sf


#SampleFile = Base.classes.sample_file
#SampleFile.get_files_ids = samplefile_get_files_ids
#SampleFile.get_files = samplefile_get_files
#SampleFile.save = generic_save
#SampleFile.new = samplefile_new










# =====================================================================================================================
# SAMPLE VARIANT
# =====================================================================================================================

class SampleVariant:
    # TODO : create property dynamicaly according to available reference in the database
    _hg19 = Base.classes.sample_variant_hg19
    
    
    def get_sample(self, variant_id, ref_id=2):
        pass
    
    def get_variants_ids(self, sample_id, ref_id=2):
        pass
    
    
    def get_variants(self, sample_id):
        pass
    
    
    def new(self, sample_id, variant_id):
        pass