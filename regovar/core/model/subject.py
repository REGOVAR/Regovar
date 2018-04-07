#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *





def subject_init(self, loading_depth=0, force=False):
    """
        Init properties of a subject :
            - id            : int           : the unique id of the subject in the database
            - identifier    : str           : the identifier of the subject
            - comment       : str           : an optional comment
            - firstname     : str           : The firstname
            - lastname      : str           : The lastname
            - sex           : enum          : The sex
            - family_number : str           : A custom family number
            - dateofbirth   : datetime      : The dateofbirth of the subject
            - dateofdeath   : datetime      : The deathday of the subject
            - update_date   : date          : The last time that the object have been updated
            - create_date   : date          : The datetime when the object have been created
            - jobs_ids      : [int]         : The list of ids of jobs with subject's files as inputs
            - analyses_ids  : [int]         : The list of ids of analyses that are using subject's sample as inputs
            - samples_ids   : [int]         : The list of ids of samples of the subject
            - files_ids     : [int]         : The list of ids of files that contains the subject
            - hpo_ids       : [str]         : The list of ids of phenotypes associated to the subject
            - projects_ids  : [int]         : The list of ids of projects associated to the subject
            - indicators    : [Indicator]   : The list of Indicator define for this subject
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - jobs          : [Job]         : The list of Job with subject's files as inputs
            - samples       : [Sample]      : The list of Sample owns by the subject
            - analyses      : [Analysis]    : The list of Analysis that are using subject's sample as inputs
            - files         : [File]        : The list of File owns by the subject
            - hpo           : [json]        : The list of phenotypes associated to the subject
            - projects      : [Project]     : The list of Project that contains this subject
            - events        : [json]        : The list of events linked to this subject
    """
    from core.model.indicator import Indicator
    from core.core import core
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    # Avoid recursion infinit loop
    if hasattr(self, "loading_depth") and self.loading_depth >= loading_depth:
        return
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        self.indicators= Indicator.from_subject_id(self.id)
        self.samples_ids = [r.id for r in execute("SELECT id FROM sample WHERE subject_id={}".format(self.id))]
        self.files_ids = [r.id for r in execute("SELECT file_id FROM subject_file WHERE subject_id={}".format(self.id))]
        self.projects_ids = self.get_projects_ids()
        self.hpo_ids = self.get_phenotypes_ids()
        self.analyses_ids = []
        self.jobs_ids = []

        if len(self.samples_ids) > 0:
            self.analyses_ids = [r.analysis_id for r in execute("SELECT analysis_id FROM analysis_sample WHERE sample_id IN ({})".format(','.join([str(i) for i in self.samples_ids])))]
        files_ids = self.files_ids
        files_ids.extend([r.file_id for r in execute("SELECT file_id FROM sample WHERE subject_id={}".format(self.id))])
        if len(files_ids) > 0:
            self.jobs_ids = [r.job_id for r in execute("SELECT job_id FROM job_file WHERE file_id IN ({})".format(','.join([str(i) for i in files_ids])))]
        
        self.jobs = []
        self.samples = []
        self.analyses = []
        self.files = []
        self.hpo = []
        self.projects = []
        self.events = []
        if self.loading_depth > 0:
            self.samples = self.get_samples(self.loading_depth-1)
            self.jobs = self.get_jobs(self.loading_depth-1)
            self.analyses = self.get_analyses(self.loading_depth-1)
            self.files = self.get_files(self.loading_depth-1)
            self.hpo = self.get_phenotypes()
            self.projects = self.get_projects(self.loading_depth-1)
            self.events = core.events.list(subject_id=self.id)
    except Exception as ex:
        raise RegovarException("subject data corrupted (id={}).".format(self.id), "", ex)



def subject_from_id(subject_id, loading_depth=0):
    """
        Retrieve subject with the provided id in the database
    """
    subject = Session().query(Subject).filter_by(id=subject_id).first()
    if subject:
        Session().refresh(subject)
        subject.init(loading_depth)
    return subject


def subject_from_ids(subject_ids, loading_depth=0):
    """
        Retrieve subjects corresponding to the list of provided id
    """
    subjects = []
    if subject_ids and len(subject_ids) > 0:
        subjects = Session().query(Subject).filter(Subject.id.in_(subject_ids)).all()
        for f in subjects:
            Session().refresh(f)
            f.init(loading_depth)
    return subjects


def subject_to_json(self, fields=None, loading_depth=-1):
    """
        Export the subject into json format with only requested fields
    """
    result = {}
    if loading_depth < 0:
        loading_depth = self.loading_depth
    if fields is None:
        fields = Subject.public_fields
    for f in fields:
        if f in Subject.public_fields:
            if f in ["create_date", "update_date", "dateofbirth", "dateofdeath"] and hasattr(self, f) and eval("self." + f):
                result[f] = eval("self." + f + ".isoformat()")
            elif f in ["jobs", "analyses", "files", "projects", "samples", "indicators"] and hasattr(self, f):
                if hasattr(self, f) and len(eval("self." + f)) > 0 and loading_depth > 0:
                    result[f] = [o.to_json(None, loading_depth-1) for o in eval("self." + f)]
                else :                           
                    result[f] = []
            elif hasattr(self, f):
                result[f] = eval("self." + f)
    return result


def subject_load(self, data):
    try:
        # Required fields
        if "identifier" in data.keys(): self.identifier = check_string(data['identifier'])
        if "comment" in data.keys(): self.comment = check_string(data['comment'])
        if "firstname" in data.keys(): self.firstname = check_string(data['firstname'])
        if "lastname" in data.keys(): self.lastname = check_string(data['lastname'])
        if "family_number" in data.keys(): self.family_number = check_string(data['family_number'])
        if "sex" in data.keys() and data['sex'] in ["male", "female", "unknow"]: self.sex = data['sex']
        if "dateofbirth" in data.keys(): self.dateofbirth = check_date(data['dateofbirth'])
        if "dateofdeath" in data.keys(): self.dateofdeath = check_date(data['dateofdeath'])
        if "update_date" in data.keys(): self.update_date = check_date(data['update_date'])
        self.save()
        
        # TODO : update indicators
        
        # update files linkeds
        if "files_ids" in data.keys():
            # Delete all associations
            Session().query(SubjectFile).filter_by(subject_id=self.id).delete(synchronize_session=False)
            # Create new associations
            self.files_ids = data["files_ids"]
            for fid in data["files_ids"]:
                SubjectFile.set(self.id, fid)
        # update phenotype linkeds
        if "hpo_ids" in data.keys():
            # Delete all associations
            Session().query(SubjectPhenotype).filter_by(subject_id=self.id).delete(synchronize_session=False)
            # Create new associations
            self.hpo_ids = data["hpo_ids"]
            for pid in data["hpo_ids"]:
                SubjectPhenotype.set(self.id, pid)
                    

            
            # Create new associations
            self.files_ids = data["files_ids"]
            for fid in data["files_ids"]:
                SubjectFile.set(self.id, fid)

        # TODO : projects
        # TODO : samples

        # check to reload dynamics properties
        self.init(self.loading_depth, True)
    except KeyError as e:
        raise RegovarException('Invalid input subject: missing ' + e.args[0])
    return self


def subject_save(self):
    generic_save(self)


def subject_delete(subject_id):
    """
        Delete the subject with the provided id in the database
    """
    Session().query(Subject).filter_by(id=subject_id).delete(synchronize_session=False)
    # TODO: delete indicator


def subject_new():
    """
        Create a new subject and init/synchronise it with the database
    """
    s = Subject()
    s.save()
    s.init()
    return s


def subject_count():
    """
        Return total of Subject entries in database
    """
    return generic_count(Subject)






def subject_get_samples_ids(self):
    """
        Return the list of samples id that concerned the subject
    """
    result = []
    samples = Session().query(Sample).filter_by(subject_id=self.id).order_by(Sample.id).all()
    for s in samples:
        result.append(s.id)
    return result

def subject_get_analyses(self, loading_depth=0):
    """
        Return the list of analyses linked to the subject (ie analyses that are using subject's samples as inputs)
    """
    from core.model.sample import Sample
    from core.model.analysis import Analysis, AnalysisSample
    
    samples = Session().query(Sample).filter_by(subject_id=self.id).all()
    samples_ids = [s.id for s in samples]
    analyses = []
    if len(samples_ids) > 0:
        analyses_ids = Session().query(AnalysisSample).filter(AnalysisSample.sample_id.in_(samples_ids)).all()
        analyses_ids = [i.analysis_id for i in analyses_ids]
        if len(analyses_ids) > 0:
            analyses = Session().query(Analysis).filter(Analysis.id.in_(analyses_ids)).all()
    
    for a in analyses: a.init(loading_depth)
    return analyses



def subject_get_samples(self, loading_depth=0):
    """
        Return the list of samples linked to the subject
    """
    from core.model.sample import Sample
    samples = Session().query(Sample).filter_by(subject_id=self.id).all()
    for s in samples: s.init(loading_depth)
    return samples



def subject_get_jobs(self, loading_depth=0):
    """
        Return the list of jobs linked to the subject (ie jobs that are using subject's files as inputs)
    """
    from core.model.file import File
    from core.model.job import Job, JobFile
    
    files = Session().query(SubjectFile).filter_by(subject_id=self.id).all()
    files_ids = [f.file_id for f in files]
    jobs = []
    for fid in files_ids:
        jobs.extend(JobFile.get_jobs(fid))
    return jobs



def subject_get_files(self, loading_depth=0):
    """
        Return the list of files linked to the subject
    """
    from core.model.file import File
    ids = Session().query(SubjectFile).filter_by(subject_id=self.id).all()
    return File.from_ids([i.file_id for i in ids], loading_depth)


def subject_get_phenotypes_ids(self):
    """
        Return the list of phenotypes ids linked to the subject
    """
    sql  = "SELECT hpo_id FROM subject_phenotype WHERE subject_id={}".format(self.id)
    return [r.id for r in execute(sql)]


def subject_get_phenotypes(self):
    """
        Return the list of phenotypes ids linked to the subject
    """
    result = []
    sql = "SELECT h.hpo_id, h.label, h.definition, h.allsubs_genes, h.allsubs_diseases, h.allsubs_genes_count, h.allsubs_diseases_count, h.allsubs_count "
    sql += " FROM hpo_term h INNER JOIN subject_phenotype s ON s.hpo_id=h.hpo_id WHERE s.subject_id={}".format(self.id)
    for r in execute(sql):
        r.append({"id": r.hpo_id, "label": r.label})
        row = execute(sql).first()
        result = {
            "id": hpo_id,
            "type" : "phenotype",
            "label": row.label,
            "definition": row.definition,
            "parent": None,
            "childs": [],
            "diseases": {},
            "genes": []
        }

    sql  = "SELECT hpo_id, label, definition,  FROM subject_phenotype WHERE subject_id={}".format(self.id)
    return [r.id for r in execute(sql)]


def subject_get_projects_ids(self):
    """
        Return the list of projects ids linked to the subject
    """
    sql  = "SELECT distinct(t3.id) FROM project t3 INNER JOIN analysis t2 ON t3.id=t2.project_id "
    sql += "INNER JOIN analysis_sample t1 ON t2.id=t1.analysis_id INNER JOIN sample t0 ON t1.sample_id=t0.id "
    sql += "WHERE t0.subject_id={}"
    return [r.id for r in execute(sql.format(self.id))]

def subject_get_projects(self, loading_depth=0):
    """
        Return the list of projects linked to the subject
    """
    from core.model.project import Project
    return Project.from_ids(self.get_projects_ids(), loading_depth)





Subject = Base.classes.subject
Subject.public_fields = ["id", "identifier", "firstname", "lastname", "sex", "comment", "dateofbirth", "dateofdeath", "create_date", "family_number", "update_date", "jobs_ids", "samples_ids", "files_ids", "analyses_ids", "projects_ids", "jobs", "samples", "analyses", "files", "indicators", "projects_ids", "projects", "events"]
Subject.init = subject_init
Subject.from_id = subject_from_id
Subject.from_ids = subject_from_ids
Subject.to_json = subject_to_json
Subject.load = subject_load
Subject.save = subject_save
Subject.new = subject_new
Subject.delete = subject_delete
Subject.count = subject_count
Subject.get_jobs = subject_get_jobs
Subject.get_samples = subject_get_samples
Subject.get_samples_ids = subject_get_samples_ids
Subject.get_projects_ids = subject_get_projects_ids
Subject.get_projects = subject_get_projects
Subject.get_analyses = subject_get_analyses
Subject.get_files = subject_get_files
Subject.get_phenotypes_ids = subject_get_phenotypes_ids
Subject.get_phenotypes = subject_get_phenotypes








# =====================================================================================================================
# SUBJECT FILES associations
# =====================================================================================================================

def sf_set(subject_id, file_id):
    """
        Create or update the link between subject and the file
    """
    # Get or create the association
    sf = Session().query(SubjectFile).filter_by(subject_id=subject_id, file_id=file_id).first()
    if not sf: 
        sf = SubjectFile(subject_id=subject_id, file_id=file_id)
        sf.save()
    return sf



def sf_unset(subject_id, file_id):
    """
        Delete a the link between the subject and the file
    """
    Session().query(SubjectFile).filter_by(subject_id=subject_id, file_id=file_id).delete(synchronize_session=False)



def sf_save(self):
    generic_save(self)


SubjectFile = Base.classes.subject_file
SubjectFile.set = sf_set
SubjectFile.unset = sf_unset
SubjectFile.save = sf_save



# =====================================================================================================================
# SUBJECT PHENOTYPE associations
# =====================================================================================================================

def sp_set(subject_id, hpo_id):
    """
        Create or update the link between subject and the phenotype
    """
    # Get or create the association
    sp = Session().query(SubjectPhenotype).filter_by(subject_id=subject_id, hpo_id=hpo_id).first()
    if not sp: 
        sp = SubjectPhenotype(subject_id=subject_id, hpo_id=hpo_id)
        sp.save()
    return sp



def sp_unset(subject_id, file_id):
    """
        Delete a the link between the subject and the phenotype
    """
    Session().query(SubjectPhenotype).filter_by(subject_id=subject_id, file_id=file_id).delete(synchronize_session=False)



def sp_save(self):
    generic_save(self)


SubjectPhenotype = Base.classes.subject_phenotype
SubjectPhenotype.set = sp_set
SubjectPhenotype.unset = sp_unset
SubjectPhenotype.save = sp_save

