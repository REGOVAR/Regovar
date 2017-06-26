#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *



def file_init(self, loading_depth=0):
    """
        If loading_depth is > 0, children objects will be loaded. Max depth level is 2.
        Children objects of a file are :
            - job_source : set with a Job object if the file have been created by a job. 
            - jobs       : the list of jobs in which the file is used or created
        If loading_depth == 0, children objects are not loaded
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
    file = session().query(File).filter_by(id=file_id).first()
    if file:
        file.init(loading_depth)
    return file


def file_from_ids(file_ids, loading_depth=0):
    """
        Retrieve files corresponding to the list of provided id
    """
    files = []
    if file_ids and len(file_ids) > 0:
        files = session().query(File).filter(File.id.in_(file_ids)).all()
        for f in files:
            f.init(loading_depth)
    return files


def file_to_json(self, fields=None):
    """
        Export the file into json format with requested fields
    """
    result = {}
    if fields is None:
        fields = ["id", "name", "type", "size", "upload_offset", "status", "create_date", "update_date", "tags", "job_source_id", "jobs_ids"]
    for f in fields:
        if f == "create_date" or f == "update_date":
            result.update({f: eval("self." + f + ".ctime()")})
        elif f == "jobs":
            if self.loading_depth == 0:
                result.update({"jobs" : self.jobs})
            else:
                result.update({"jobs" : [j.to_json() for j in self.jobs]})
        elif f == "job_source" and self.loading_depth > 0:
            if self.job_source:
                result.update({"job_source" : self.job_source.to_json()})
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
        if "name"          in data.keys(): self.name           = data['name']
        if "type"          in data.keys(): self.type           = data['type']
        if "path"          in data.keys(): self.path           = data['path']
        if "size"          in data.keys(): self.size           = int(data["size"])
        if "upload_offset" in data.keys(): self.upload_offset  = int(data["upload_offset"])
        if "status"        in data.keys(): self.status         = data['status']
        if "create_date"   in data.keys(): self.create_date    = data['create_date']
        if "update_date"   in data.keys(): self.update_date    = data['update_date']
        if "md5sum"        in data.keys(): self.md5sum         = data["md5sum"]
        if "tags"          in data.keys(): self.tags           = data['tags']
        if "job_source_id" in data.keys(): self.job_source_id  = int(data["job_source_id"])
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
    session().query(File).filter_by(id=file_id).delete(synchronize_session=False)


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
File.to_json = file_to_json
File.load = file_load
File.save = generic_save
File.delete = file_delete
File.new = file_new
File.count = file_count
 
