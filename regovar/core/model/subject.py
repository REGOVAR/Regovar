#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *





def subject_init(self, loading_depth=0, force=False):
    """
        Init properties of a subject :
            - id            : int           : the unique id of the subject in the database
            - identifiant   : str           : the identifiant of the subject
            - comment       : str           : an optional comment
            - firstname     : str           : The firstname
            - lastname      : str           : The lastname
            - sex           : enum          : The sex
            - birthday      : datetime      : The birthday of the subject
            - deathday      : datetime      : The dethday of the subject
            - update_date   : date          : The last time that the object have been updated
            - jobs_ids      : [int]         : The list of ids of jobs with subject's files as inputs
            - analyses_ids  : [int]         : The list of ids of analyses that are using subject's sample as inputs
            - samples_ids   : [int]         : The list of ids of samples of the subject
            - files_ids     : [int]         : The list of ids of files that contains the subject
            - projects_ids  : [int]         : The list of ids of projects associated to the subject
            - indicators    : [Indicator]   : The list of Indicator define for this subject
            - users         : [Users]       : The list of Users that can access to the subject
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - jobs          : [Job]         : The list of Job with subject's files as inputs
            - samples       : [Sample]      : The list of Sample owns by the subject
            - analyses      : [Analysis]    : The list of Analysis that are using subject's sample as inputs
            - files         : [File]        : The list of File owns by the subject
            - projects      : [Project]     : The list of Project that contains this subject
    """
    # Avoid recursion infinit loop
    if hasattr(self, "loading_depth") and not force:
        return
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        self.indicators= self.get_indicators()
        self.projects_ids = [s.id for s in self.get_projects()]
        self.jobs_ids = [j.id for j in self.get_jobs()]
        self.analyses_ids = [a.id for a in self.get_analyses()]
        self.files_ids = [f.id for f in self.get_files()]
        self.samples_ids = [s.id for s in self.get_samples()]
        self.users = self.get_users()
        
        self.jobs = []
        self.samples = []
        self.analyses = []
        self.files = []
        self.projects = []
        if self.loading_depth > 0:
            self.samples = self.get_samples(self.loading_depth-1)
            self.jobs = self.get_jobs(self.loading_depth-1)
            self.analyses = self.get_analyses(self.loading_depth-1)
            self.files = self.get_files(self.loading_depth-1)
            self.projects = self.get_projects(self.loading_depth-1)
    except Exception as ex:
        raise RegovarException("subject data corrupted (id={}).".format(self.id), "", ex)



def subject_from_id(subject_id, loading_depth=0):
    """
        Retrieve subject with the provided id in the database
    """
    subject = session().query(Subject).filter_by(id=subject_id).first()
    if subject:
        subject.init(loading_depth)
    return subject


def subject_from_ids(subject_ids, loading_depth=0):
    """
        Retrieve subjects corresponding to the list of provided id
    """
    subjects = []
    if subject_ids and len(subject_ids) > 0:
        subjects = session().query(Subject).filter(Subject.id.in_(subject_ids)).all()
        for f in subjects:
            f.init(loading_depth)
    return subjects


def subject_to_json(self, fields=None):
    """
        Export the subject into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Subject.public_fields
    for f in fields:
        if f in Subject.public_fields:
            if f in ["create_date", "update_date"] :
                result.update({f: eval("self." + f + ".isoformat()")})
            elif f in ["jobs", "analyses", "files", "projects", "samples", "indicators"]:
                result[f] = [o.to_json() for o in eval("self." + f)]
            else:
                result.update({f: eval("self." + f)})
    return result


def subject_load(self, data):
    try:
        # Required fields
        if "identifiant" in data.keys(): self.identifiant = data['identifiant']
        if "comment" in data.keys(): self.comment = data['comment']
        if "firstname" in data.keys(): self.firstname = data['firstname']
        if "lastname" in data.keys(): self.lastname = data['lastname']
        if "sex" in data.keys() and data['sex'] in ["male", "female", "unknow"]: self.sex = data['sex']
        if "birthday" in data.keys(): self.birthday = data['birthday']
        if "deathday" in data.keys(): self.deathday = data['deathday']
        if "update_date" in data.keys(): self.update_date = data['update_date']
        if "last_activity" in data.keys(): self.last_activity = data['last_activity']
        self.save()
        
        # TODO : update indicators
        # Update user sharing
        if "users" in data.keys():
            # Delete all associations
            session().query(UserSubjectSharing).filter_by(subject_id=self.id).delete(synchronize_session=False)
            # Create new associations
            self.users = data["users"]
            for u in data["users"]:
                if isinstance(u, dict) and "id" in u.keys() and "write_authorisation" in u.keys():
                    UserProjectSubring.set(self.id, u["id"], u["write_authorisation"])
                else:
                    err("Wrong User sharing token for the Subject")
        
        # update files linkeds
        if "files_ids" in data.keys():
            # Delete all associations
            session().query(SubjectFile).filter_by(subject_id=self.id).delete(synchronize_session=False)
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
    session().query(SubjectIndicator).filter_by(subject_id=subject_id).delete(synchronize_session=False)
    session().query(UserSubjectSharing).filter_by(subject_id=subject_id).delete(synchronize_session=False)
    session().query(Subject).filter_by(id=subject_id).delete(synchronize_session=False)


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





def subject_get_indicators(self, loading_depth=0):
    """
        Return the list of indicators for the subject
    """
    from core.model.indicator import Indicator
    indicators = session().query(SubjectIndicator).filter_by(subject_id=self.id).all()
    return indicators



def subject_get_analyses(self, loading_depth=0):
    """
        Return the list of analyses linked to the subject (ie analyses that are using subject's samples as inputs)
    """
    from core.model.sample import Sample
    from core.model.analysis import Analysis, AnalysisSample
    
    samples = session().query(Sample).filter_by(subject_id=self.id).all()
    samples_ids = [s.id for s in samples]
    analyses = []
    if len(samples_ids) > 0:
        analyses_ids = session().query(AnalysisSample).filter(AnalysisSample.sample_id.in_(samples_ids)).all()
        analyses_ids = [i.analysis_id for i in analyses_ids]
        if len(analyses_ids) > 0:
            analyses = session().query(Analysis).filter(Analysis.id.in_(analyses_ids)).all()
    
    for a in analyses: a.init(loading_depth)
    return analyses



def subject_get_samples(self, loading_depth=0):
    """
        Return the list of samples linked to the subject
    """
    from core.model.sample import Sample
    samples = session().query(Sample).filter_by(subject_id=self.id).all()
    for s in samples: s.init(loading_depth)
    return samples



def subject_get_jobs(self, loading_depth=0):
    """
        Return the list of jobs linked to the subject (ie jobs that are using subject's files as inputs)
    """
    from core.model.file import File
    from core.model.job import Job, JobFile
    
    files = session().query(SubjectFile).filter_by(subject_id=self.id).all()
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
    ids = session().query(SubjectFile).filter_by(subject_id=self.id).all()
    return File.from_ids([i.file_id for i in ids], loading_depth)



def subject_get_projects(self, loading_depth=0):
    """
        Return the list of projects linked to the subject
    """
    from core.model.project import Project, ProjectSubject
    ids = session().query(ProjectSubject).filter_by(subject_id=self.id).all()
    return Project.from_ids([i.project_id for i in ids], loading_depth)




def subject_get_users(self):
    """
        Return the list of users that have access to the subject
    """
    from core.model.user import User
    ussl = session().query(UserSubjectSharing).filter_by(subject_id=self.id).all()
    users_ids = [u.user_id for u in ussl]
    result = []
    for uss in ussl:
        u = session().query(User).filter_by(id=uss.user_id).first()
        if u:
            result.append({"id": u.id, "login" : u.login, "firstname": u.firstname, "lastname": u.lastname, "write_authorisation": uss.write_authorisation})
        else:
            war("User's id ({}) linked to the subject ({}), but user doesn't exists.".format(uss.user_id, self.id))
    return result






Subject = Base.classes.subject
Subject.public_fields = ["id", "identifiant", "firstname", "lastname", "sex", "comment", "birthday", "deathday", "update_date", "jobs_ids", "samples_ids", "files_ids", "analyses_ids", "jobs", "samples", "analyses", "files", "indicators", "users", "projects_ids", "projects"]
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
Subject.get_projects = subject_get_projects
Subject.get_indicators = subject_get_indicators
Subject.get_analyses = subject_get_analyses
Subject.get_files = subject_get_files
Subject.get_users = subject_get_users





# =====================================================================================================================
# SUBJECT INDICATOR associations
# =====================================================================================================================
def subjectindicator_to_json(self, fields=None):
    """
        Export the subject indicator into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = ["subject_id", "indicator_id", "indicator_value_id"]
    for f in fields:
        result.update({f: eval("self." + f)})
    return result



SubjectIndicator = Base.classes.subject_indicator
SubjectIndicator.to_json = subjectindicator_to_json




# =====================================================================================================================
# SUBJECT FILES associations
# =====================================================================================================================
def sf_new(subject_id, file_id):
    sf = SubjectFile(subject_id=subject_id, file_id=file_id)
    sf.save()
    return sf

def sf_set(subject_id, file_id):
    """
        Create or update the link between subject and the file
    """
    # Get or create the association
    sf = session().query(SubjectFile).filter_by(subject_id=subject_id, file_id=file_id).first()
    if not sf: 
        sf = SubjectFile(subject_id=subject_id, file_id=file_id)
        sf.save()
    return sf



def sf_unset(subject_id, file_id):
    """
        Delete a the link between the subject and the file
    """
    session().query(SubjectFile).filter_by(subject_id=subject_id, file_id=file_id).delete(synchronize_session=False)



def sf_save(self):
    generic_save(self)


SubjectFile = Base.classes.subject_file
SubjectFile.set = sf_set
SubjectFile.unset = sf_unset
SubjectFile.save = sf_save







# =====================================================================================================================
# SUBJECT USERS associations
# =====================================================================================================================
def uss_get_auth(subject_id, user_id):
    uss = session().query(UserSubjectSharing).filter_by(subject_id=subject_id, user_id=user_id).first()
    if uss : 
        return uss.write_authorisation
    return None


def uss_set(subject_id, user_id, write_authorisation):
    """
        Create or update the sharing option between subject and user
    """
    # Get or create the association
    uss = session().query(UserSubjectSharing).filter_by(subject_id=subject_id, user_id=user_id).first()
    if not uss: uss = UserSubjectSharing()
    
    # Update the association     
    uss.subject_id=subject_id
    uss.user_id=user_id
    uss.write_authorisation=write_authorisation
    uss.save()
    return uss



def uss_unset(subject_id, user_id):
    """
        Delete a the sharing option between the subject and the user
    """
    session().query(UserSubjectSharing).filter_by(subject_id=subject_id, user_id=user_id).delete(synchronize_session=False)
    


def uss_save(self):
    generic_save(self)


UserSubjectSharing = Base.classes.user_subject_sharing
UserSubjectSharing.get_auth = uss_get_auth
UserSubjectSharing.set = uss_set
UserSubjectSharing.unset = uss_unset
UserSubjectSharing.save = uss_save
