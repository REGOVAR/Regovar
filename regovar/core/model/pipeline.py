#!env/python3
# coding: utf-8
import ipdb
import os
import json


from core.framework.common import *
from core.framework.postgresql import *






def pipeline_init(self, loading_depth=0):
    """
        If loading_depth is > 0, children objects will be loaded. Max depth level is 2.
        Child object of a pipeline is :
            - "image_file" : the file of the pipeline image (if exists)
            - "jobs" property which contains the list of jobs that use the pipeline

        If loading_depth == 0, child object are not loaded, so jobs will be set with the  list of job's id
    """
    from core.model.job import Job
    self.jobs_ids = []
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)

    jobs = session().query(Job).filter_by(pipeline_id=self.id).all()
    for j in jobs:
        self.jobs_ids.append(j.id)
    self.load_depth(loading_depth)
            

def pipeline_load_depth(self, loading_depth):
    from core.model.job import Job
    from core.model.file import File
    if loading_depth > 0:
        try:
            self.image_file = None
            self.image_file = File.from_id(self.image_file_id, self.loading_depth-1)
            self.jobs = []
            if len(self.jobs_ids) > 0:
                self.jobs = session().query(Job).filter(Job.id.in_(self.jobs_ids)).all()
                for j in self.jobs:
                    j.init(loading_depth-1)
        except Exception as err:
            raise RegovarException("File data corrupted (id={}).".format(self.id), "", err)



def pipeline_from_id(pipeline_id, loading_depth=0):
    """
        Retrieve pipeline with the provided id in the database
    """
    pipeline = session().query(Pipeline).filter_by(id=pipeline_id).first()
    if pipeline:
        pipeline.init(loading_depth)
    return pipeline


def pipeline_from_ids(pipeline_ids, loading_depth=0):
    """
        Retrieve pipelines corresponding to the list of provided id
    """
    pipelines = []
    if pipeline_ids and len(pipeline_ids) > 0:
        pipelines = session().query(Pipeline).filter(Pipeline.id.in_(pipeline_ids)).all()
        for p in pipelines:
            p.init(loading_depth)
    return pipelines


def pipeline_to_json(self, fields=None):
    """
        Export the pipeline into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = ["id", "name", "type", "status", "description", "developers", "installation_date", "version", "pirus_api", "image_file_id", "manifest", "documents"]
    for f in fields:
        if f == "installation_date":
            result.update({f: eval("self." + f + ".ctime()")})
        elif f == "jobs":
            if self.jobs and self.loading_depth > 0:
                result.update({"jobs" : [j.to_json() for j in self.jobs]})
            else:
                result.update({"jobs" : self.jobs})
        elif f == "manifest" and self.manifest:
            result.update({"manifest" : json.loads(self.manifest)})
        elif f == "documents" and self.documents:
            result.update({"documents" : json.loads(self.documents)})
        elif f == "image_file" and self.image_file:
            result.update({f: self.image_file.to_json()})
        else:
            result.update({f: eval("self." + f)})
    return result


def pipeline_load(self, data):
    try:
        # Required fields
        if "name" in data.keys(): self.name = data['name']
        if "type" in data.keys(): self.type = data["type"]
        if "status" in data.keys(): self.status = data["status"]
        if "description" in data.keys(): self.description = data["description"]
        if "developers" in data.keys(): self.developers = data["developers"]
        if "installation_date" in data.keys(): self.installation_date = data["installation_date"]
        if "version" in data.keys(): self.version = data['version']
        if "pirus_api" in data.keys(): self.pirus_api = data["pirus_api"]
        if "image_file_id" in data.keys(): self.image_file_id = data["image_file_id"]
        if "manifest" in data.keys(): self.manifest = data['manifest']
        if "documents" in data.keys(): self.documents = data['documents']
        if "path" in data.keys(): self.path = data['path']
        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.load_depth(self.loading_depth)
        self.save()
    except KeyError as e:
        raise RegovarException('Invalid input pipeline: missing ' + e.args[0])
    return self


def pipeline_delete(pipeline_id):
    """
        Delete the pipeline with the provided id in the database
    """
    try:
        session().query(Pipeline).filter_by(id=pipeline_id).delete(synchronize_session=False)
        session().commit()
    except Exception as ex:
        err("Unable to remove pipe from database", ex)


def pipeline_new():
    """
        Create a new file and init/synchronise it with the database
    """
    p = Pipeline()
    p.save()
    p.init()
    return p


def pipeline_count():
    """
        Return total of Pipeline entries in database
    """
    return generic_count(Pipeline)


Pipeline = Base.classes.pipeline
Pipeline.public_fields = ["id", "name", "type", "status", "description", "developers", "installation_date", "version", "pirus_api", "image_file_id", "image_file", "manifest", "documents", "path", "jobs_ids", "jobs"]
Pipeline.init = pipeline_init
Pipeline.load_depth = pipeline_load_depth
Pipeline.from_id = pipeline_from_id
Pipeline.from_ids = pipeline_from_ids
Pipeline.to_json = pipeline_to_json
Pipeline.load = pipeline_load
Pipeline.save = generic_save
Pipeline.delete = pipeline_delete
Pipeline.new = pipeline_new
Pipeline.count = pipeline_count 
