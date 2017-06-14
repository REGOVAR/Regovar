#!env/python3
# coding: utf-8
import os
import json


from core.framework.common import *
from core.framework.postgresql import *




 
def project_init(self, loading_depth=0):
    """
        If loading_depth is > 0, children objects will be loaded. Max depth level is 2.
        Children objects of a project are :
            - indicators : project's custom indicators
            - jobs_ids
            - analyses_ids
            - files_ids
            - users_ids

        If loading_depth == 0, children objects are not loaded, so source will be set with the id of the project if exists
    """
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        self.indicators=[]
        self.subjects_ids = []
        self.jobs_ids = [j.id for j in self.get_jobs()]
        self.analyses_ids = [a.id for a in self.get_analyses()]
        self.files_ids = [f.id for f in self.get_files()]
        self.users = self.get_users()
    except Exception as ex:
        raise RegovarException("Project data corrupted (id={}).".format(self.id), "", ex)
    
    self.load_depth()
            




def project_load_depth(self):
    self.jobs = None
    self.analyses = None
    self.files = None
    if self.loading_depth > 0:
        try:
            self.jobs = self.get_jobs(self.loading_depth-1)
            self.analyses = self.get_analyses(self.loading_depth-1)
            self.files = self.get_files(self.loading_depth-1)
        except Exception as ex:
            raise RegovarException("Project data corrupted (id={}).".format(self.id), "", ex)





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
        fields = ["id", "name", "comment", "parent_id", "is_folder", "last_activity", "jobs_ids", "files_ids", "analyses_ids", "indicators", "users", "is_sandbox"]
    for f in fields:
        if f == "last_activity" :
            result.update({f: eval("self." + f + ".ctime()")})
        else:
            result.update({f: eval("self." + f)})
    return result


def project_load(self, data):
    try:
        # Required fields
        if "name" in data.keys(): self.name = data['name']
        if "comment" in data.keys(): self.comment = data['comment']
        if "parent_id" in data.keys(): self.parent_id = data['parent_id']
        if "is_folder" in data.keys(): self.is_folder = data['is_folder']
        if "last_activity" in data.keys(): self.last_activity = data['last_activity']
        if "is_sandbox" in data.keys(): self.is_sandbox = data['is_sandbox']
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


def project_new():
    """
        Create a new project and init/synchronise it with the database
    """
    p = Project()
    p.save()
    p.init()
    return p


def project_count():
    """
        Return total of Job entries in database
    """
    return generic_count(Project)



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
    return session().query(Analysis).filter_by(project_id=self.id).all()



def projects_get_files(self, loading_depth=0):
    """
        Return the list of files linked to the project
    """
    from core.model.file import File
    files_ids = [pf.file_id for pf in session().query(ProjectFile).filter_by(project_id=self.id).all()]
    if len(files_ids) > 0:
        return session().query(File).filter(File.id.in_(files_ids)).all()
    return []



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
            war("User's id ({}) linked to the project ({}), but user doesn't exists.".format(u.id, self.id))
    return result






Project = Base.classes.project
Project.public_fields = ["id", "name", "comment", "parent_id", "is_folder", "last_activity", "jobs_ids", "files_ids", "analyses_ids", "indicators", "users", "is_sandbox"]
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
Project.get_users = projects_get_users







# =====================================================================================================================
# PROJECT INDICATOR associations
# =====================================================================================================================
ProjectIndicator = Base.classes.project_indicator




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





