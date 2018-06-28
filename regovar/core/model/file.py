#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *



def file_init(self, loading_depth=0):
    """
        Init properties of a File :
            - id               : int        : the unique id of the file in the database
            - name             : str        : the name of the file
            - type             : str        : the file type (file extension)
            - comment          : str        : a comment on the file
            - path             : str        : the path to the file on the server (must be convert to public url if needed)
            - size             : int        : the total size (in bytes) of the file
            - upload_offset    : int        : the size of uploaded bytes of the file
            - status           : enum       : status values can be : 'uploading', 'uploaded', 'checked', 'error'
            - update_date      : date       : The last time that the object have been updated
            - create_date      : date       : The datetime when the object have been created
            - reference_id     : int        : the reference id for this sample
            - tags             : [str]      : list of custom tags set by users to help search and retrieve files
            - md5sum           : str        : the md5sum of the file on the server
            - job_source_id    : int        : id of the job that generate this file (if exists, None otherwise)
            - jobs_ids         : [int]      : the list of id of jobs that are using this file as input
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - job_source       : Job        : the job that generate this file (if exists, None otherwise)
            - jobs             : [Job]      : list of jobs that are using this file as input
    """
    from core.model.job import Job, JobFile
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    self.jobs_ids = JobFile.get_jobs_ids(self.id)
    self.load_depth(loading_depth)
            

def file_load_depth(self, loading_depth):
    from core.model.job import Job, JobFile
    if loading_depth > 0:
        try:
            self.jobs = []
            self.job_source = None
            self.job_source = Job.from_id(self.job_source_id, self.loading_depth-1)
            self.jobs = JobFile.get_jobs(self.id, self.loading_depth-1)
        except Exception as err:
            raise RegovarException("File data corrupted (id={}).".format(self.id), "", err)


def file_from_id(file_id, loading_depth=0):
    """
        Retrieve file with the provided id in the database
    """
    file = Session().query(File).filter_by(id=check_int(file_id, -1)).first()
    if file:
        Session().refresh(file)
        file.init(loading_depth)
    return file


def file_from_ids(file_ids, loading_depth=0):
    """
        Retrieve files corresponding to the list of provided id
    """
    files = []
    if file_ids and len(file_ids) > 0:
        files = Session().query(File).filter(File.id.in_(file_ids)).all()
        for f in files:
            Session().refresh(f)
            f.init(loading_depth)
    return files

def file_from_name(filename, loading_depth=0):
    """
        Retrieve file with the provided name in the database
    """
    file = Session().query(File).filter_by(name=check_string(filename)).first()
    if file:
        Session().refresh(file)
        file.init(loading_depth)
    return file


def file_to_json(self, fields=None, loading_depth=-1):
    """
        Export the file into json format with requested fields
    """
    result = {}
    if loading_depth < 0:
        loading_depth = self.loading_depth
    if fields is None:
        fields = ["id", "name", "type", "size", "upload_offset", "status", "create_date", "update_date", "tags", "job_source_id", "jobs_ids", "path"]
    for f in fields:
        if f == "create_date" or f == "update_date":
            result.update({f: eval("self." + f + ".isoformat()")})
        elif f == "jobs":
            if self.loading_depth == 0:
                result.update({"jobs" : self.jobs})
            else:
                result.update({"jobs" : [j.to_json(None, loading_depth-1) for j in self.jobs]})
        elif f == "job_source" and self.loading_depth > 0:
            if self.job_source:
                result.update({"job_source" : self.job_source.to_json(None, loading_depth-1)})
            else:
                result.update({"job_source" : self.job_source})
        else:
            result.update({f: eval("self." + f)})
    return result


def file_load(self, data):
    """
        Helper to update several paramters at the same time. Note that dynamics properties like job_source and jobs
        cannot be updated with this method. However, you can update job_source_id.
        jobs list cannot be edited from the file, each run have to be edited
    """
    try:
        if "name" in data.keys(): self.name = check_string(data['name'])
        if "type" in data.keys(): self.type = check_string(data['type'])
        if "path" in data.keys(): self.path = check_string(data['path'])
        if "size" in data.keys(): self.size = check_int(data["size"])
        if "upload_offset" in data.keys(): self.upload_offset = check_int(data["upload_offset"])
        if "status" in data.keys(): self.status = check_string(data['status'])
        if "create_date" in data.keys(): self.create_date = check_date(data['create_date'])
        if "update_date" in data.keys(): self.update_date = check_date(data['update_date'])
        if "md5sum" in data.keys(): self.md5sum = check_string(data["md5sum"])
        if "tags" in data.keys(): self.tags = data['tags']
        if "job_source_id" in data.keys(): self.job_source_id = check_int(data["job_source_id"])
        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.load_depth(self.loading_depth)
        self.save()
    except Exception as err:
        raise RegovarException('Invalid input data to load.', "", err)
    return self



def file_delete(file_id):
    """
        Delete the file with the provided id in the database
    """
    Session().query(File).filter_by(id=file_id).delete(synchronize_session=False)
    # TODO: check and clean all associations
    # - analysis via analysis_file table
    # - sample via file_id property
    # - subject via subject_file table
    # - pipeline
    # - job via job_file


def file_new():
    """
        Create a new file and init/synchronise it with the database
    """
    f = File()
    f.save()
    f.init()
    return f


def file_count():
    """
        Return total of File entries in database
    """
    return generic_count(File)


File = Base.classes.file
File.public_fields = ["id", "name", "type", "comment", "path", "size", "upload_offset", "status", "create_date", "update_date", "tags", "md5sum", "job_source_id", "jobs_ids", "job_source", "jobs"]
File.init = file_init
File.load_depth = file_load_depth
File.from_id = file_from_id
File.from_ids = file_from_ids
File.from_name = file_from_name
File.to_json = file_to_json
File.load = file_load
File.save = generic_save
File.delete = file_delete
File.new = file_new
File.count = file_count
 
