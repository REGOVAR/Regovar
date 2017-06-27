#!env/python3
# coding: utf-8
import os
import json


from core.framework.common import *
from core.framework.postgresql import *





def project_init(self, loading_depth=0):
    """
        Init properties of a project :
            - id            : int           : the unique id of the project in the database
            - name          : str           : the name of the project
            - comment       : str           : an optional comment
            - parent_id     : int           : null or refer to another project which is a folder that contains this project
            - is_folder     : bool          : True if it's a folder, False if it's a project
            - update_date   : date          : The last time that the object have been updated
            - jobs_ids      : [int]         : The list of ids of jobs that contains the project
            - files_ids     : [int]         : The list of ids of files that contains the project
            - analyses_ids  : [int]         : The list of ids of analyses that contains the project
            - subjects_ids  : [int]         : The list of ids of subjets associated to the project
            - indicators    : [Indicator]   : The list of Indicator define for this project
            - users         : [Users]       : The list of Users that can access to the project
            - is_sandbox    : bool          : True if the project is the sandbox of an user; False otherwise
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - jobs          : [Job]         : The list of Job owns by the project
            - analyses      : [Analysis]    : The list of Analysis owns by the project
            - files         : [File]        : The list of File owns by the project
            - parent        : Project       : The parent Project if defined
    """
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        self.indicators= self.get_indicators()
        self.subjects_ids = [s.id for s in self.get_subjects()]
        self.jobs_ids = [j.id for j in self.get_jobs()]
        self.analyses_ids = [a.id for a in self.get_analyses()]
        self.files_ids = [f.id for f in self.get_files()]
        self.users = self.get_users()
    except Exception as ex:
        raise RegovarException("Project data corrupted (id={}).".format(self.id), "", ex)
    self.load_depth()


def project_load_depth(self):
    self.jobs = []
    self.analyses = []
    self.files = []
    self.subjects = []
    self.parent = None
    if self.loading_depth > 0:
        self.parent = Project.from_id(self.parent_id, self.loading_depth-1)
        self.jobs = self.get_jobs(self.loading_depth-1)
        self.analyses = self.get_analyses(self.loading_depth-1)
        self.files = self.get_files(self.loading_depth-1)
        self.subjects = self.get_subjects(self.loading_depth-1)



def project_from_id(project_id, loading_depth=0):
    """
        Retrieve project with the provided id in the database
    """
    project = session().query(Project).filter_by(id=project_id).first()
    if project:
        project.init(loading_depth)
    return project


def project_from_ids(project_ids, loading_depth=0):
    """
        Retrieve projects corresponding to the list of provided id
    """
    projects = []
    if project_ids and len(project_ids) > 0:
        projects = session().query(Project).filter(Project.id.in_(project_ids)).all()
        for f in projects:
            f.init(loading_depth)
    return projects


def project_to_json(self, fields=None):
    """
        Export the project into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Project.public_fields
    for f in fields:
        if f in Project.public_fields:
            if f in ["create_date", "update_date"] :
                result.update({f: eval("self." + f + ".isoformat()")})
            elif f in ["jobs", "analyses", "files"] and self.loading_depth > 0:
                result[f] = [o.to_json() for o in eval("self." + f)]
            elif f in ["indicators"]:
                result[f] = [o.to_json() for o in eval("self." + f)]
            elif f in ["parent"] and self.loading_depth > 0 and self.parent:
                result[f] = self.parent.to_json()
            else:
                result.update({f: eval("self." + f)})
    return result



def project_load(self, data):
    """
        Helper to update project's data by loading a json.
        Note that following properties cannot be set by this ways :
            - id / is_sandbox (which MUST not be changed. this property is managfed by regovar's Model itself)
            - update_date / create_date (which are managed automaticaly by the server)
            - subjects_ids / subjects (which are too complex to be set directly. 
              Need to use UserSubjectSharing objects to update these associations)
    """
    try:
        # Required fields
        if "name" in data.keys(): self.name = data['name']
        if "comment" in data.keys(): self.comment = data['comment']
        if "parent_id" in data.keys(): self.parent_id = data['parent_id']
        if "is_folder" in data.keys(): self.is_folder = data['is_folder']
        self.save()
        
        # TODO : update indicators
        # Update user sharing
        if "users" in data.keys():
            # Delete all associations
            session().query(UserProjectSharing).filter_by(project_id=self.id).delete(synchronize_session=False)
            # Create new associations
            self.users = data["users"]
            for u in data["users"]:
                if isinstance(u, dict) and "id" in u.keys() and "write_authorisation" in u.keys():
                    UserProjectSharing.new(self.id, u["id"], u["write_authorisation"])
                else:
                    err("")
        
        # update files linkeds
        if "files_ids" in data.keys():
            # Delete all associations
            session().query(ProjectFile).filter_by(project_id=self.id).delete(synchronize_session=False)
            # Create new associations
            self.files_ids = data["files_ids"]
            for fid in data["files_ids"]:
                ProjectFile.new(self.id, fid)
        
        # TODO : update 

        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.load_depth(self.loading_depth)
    except KeyError as e:
        raise RegovarException('Invalid input project: missing ' + e.args[0])
    return self


def project_save(self):
    generic_save(self)


def project_delete(project_id):
    """
        Delete the project with the provided id in the database
    """
    session().query(ProjectIndicator).filter_by(project_id=project_id).delete(synchronize_session=False)
    session().query(UserProjectSharing).filter_by(project_id=project_id).delete(synchronize_session=False)
    session().query(ProjectFile).filter_by(project_id=project_id).delete(synchronize_session=False)
    session().query(ProjectSubject).filter_by(project_id=project_id).delete(synchronize_session=False)
    session().query(Project).filter_by(id=project_id).delete(synchronize_session=False)
    # TODO : delete analyses and job linked to the project ? that means also deleting outputs files of these jobs


def project_new():
    """
        Create a new project and init/synchronise it with the database
    """
    p = Project()
    p.save()
    p.init()
    return p


def project_count(count_folder=False, count_sandbox=False):
    """
        Return total of Job entries in database
    """
    kargs = {}
    if not count_folder: kargs["is_folder"] = False
    if not count_sandbox: kargs["is_sandbox"] = False
    
    return session().query(Project).filter_by(**kargs).count()



def projects_get_jobs(self, loading_depth=0):
    """
        Return the list of jobs linked to the project
    """
    from core.model.job import Job
    return session().query(Job).filter_by(project_id=self.id).all()



def projects_get_indicators(self, loading_depth=0):
    """
        Return the list of indicators for the project
    """
    from core.model.indicator import Indicator
    indicators = session().query(ProjectIndicator).filter_by(project_id=self.id).all()
    return indicators



def projects_get_analyses(self, loading_depth=0):
    """
        Return the list of analyses linked to the project
    """
    from core.model.analysis import Analysis
    analyses = session().query(Analysis).filter_by(project_id=self.id).all()
    for a in analyses : a.init(loading_depth)
    return analyses



def projects_get_files(self, loading_depth=0):
    """
        Return the list of files linked to the project
    """
    from core.model.file import File
    ids = session().query(ProjectFile).filter_by(project_id=self.id).all()
    return File.from_ids([i.file_id for i in ids], loading_depth)



def projects_get_subjects(self, loading_depth=0):
    """
        Return the list of subjects linked to the project
    """
    from core.model.subject import Subject
    ids = session().query(ProjectSubject).filter_by(project_id=self.id).all()
    return Subject.from_ids([i.subject_id for i in ids], loading_depth)




def projects_get_users(self):
    """
        Return the list of users that have access to the project
    """
    from core.model.user import User
    upsl = session().query(UserProjectSharing).filter_by(project_id=self.id).all()
    users_ids = [u.user_id for u in upsl]
    result = []
    for ups in upsl:
        u = session().query(User).filter_by(id=ups.user_id).first()
        if u:
            result.append({"id": u.id, "firstname": u.firstname, "lastname": u.lastname, "write_authorisation": ups.write_authorisation})
        else:
            war("User's id ({}) linked to the project ({}), but user doesn't exists.".format(ups.user_id, self.id))
    return result






Project = Base.classes.project
Project.public_fields = ["id", "name", "comment", "parent_id", "is_folder", "create_date", "update_date", "jobs_ids", "files_ids", "analyses_ids", "jobs", "analyses", "files", "indicators", "users", "is_sandbox"]
Project.init = project_init
Project.load_depth = project_load_depth
Project.from_id = project_from_id
Project.from_ids = project_from_ids
Project.to_json = project_to_json
Project.load = project_load
Project.save = project_save
Project.new = project_new
Project.delete = project_delete
Project.count = project_count
Project.get_jobs = projects_get_jobs
Project.get_indicators = projects_get_indicators
Project.get_analyses = projects_get_analyses
Project.get_files = projects_get_files
Project.get_subjects = projects_get_subjects
Project.get_users = projects_get_users







# =====================================================================================================================
# PROJECT INDICATOR associations
# =====================================================================================================================
def projectindicator_to_json(self, fields=None):
    """
        Export the project indicator into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = ["project_id", "indicator_id", "indicator_value_id"]
    for f in fields:
        result.update({f: eval("self." + f)})
    return result



ProjectIndicator = Base.classes.project_indicator
ProjectIndicator.to_json = projectindicator_to_json




# =====================================================================================================================
# PROJECT FILES associations
# =====================================================================================================================
def pf_new(project_id, file_id):
    pf = ProjectFile(project_id=project_id, file_id=file_id)
    pf.save()
    return pf


def pf_save(self):
    generic_save(self)


ProjectFile = Base.classes.project_file
ProjectFile.new = pf_new
ProjectFile.save = pf_save




# =====================================================================================================================
# PROJECT SUBJECT associations
# =====================================================================================================================
def ps_new(project_id, subject_id):
    ps = ProjectSubject(project_id=project_id, subject_id=subject_id)
    ps.save()
    return ps


def ps_save(self):
    generic_save(self)


ProjectSubject = Base.classes.project_subject
ProjectSubject.new = ps_new
ProjectSubject.save = ps_save






# =====================================================================================================================
# PROJECT USERS associations
# =====================================================================================================================
def ups_get_auth(project_id, user_id):
    ups = session().query(UserProjectSharing).filter_by(project_id=project_id, user_id=user_id).first()
    if ups : 
        return ups.write_authorisation
    return None


def ups_new(project_id, user_id, write_authorisation):
    ups = UserProjectSharing(project_id=project_id, file_id=file_id, write_authorisation=write_authorisation)
    ups.save()
    return ups


def ups_save(self):
    generic_save(self)


UserProjectSharing = Base.classes.user_project_sharing
UserProjectSharing.get_auth = ups_get_auth
UserProjectSharing.new = ups_new
UserProjectSharing.save = ups_save





