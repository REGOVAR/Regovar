#!env/python3
# coding: utf-8
import ipdb
import os
import json


from core.framework.common import *
from core.framework.postgresql import *






def pipeline_init(self, loading_depth=0, force_refresh=False):
    """
        Init properties of a Pipeline :
            - id                : int           : The unique id of the pipeline in the database
            - name              : str           : The name of the analysis
            - description       : str           : An optional description
            - type              : enum          : Enum that help the container engine to know the type of the pipeline: 'lxd', 'docker', ...
            - status            : enum          : The status of the pipeline : 'initializing', 'installing', 'ready', 'error'
            - starred           : bool          : Flag to know if the pipeline is starred or not
            - developpers       : [str]         : List of developpers of the pipeline
            - installation_date : date          : When the pipe have been installed on the server
            - version           : str           : The version of the pipeline
            - version_api       : str           : The version of the api of regovar used by the pipeline
            - image_file_id     : int           : Id of the file that was used to import/install the pipeline
            - jobs_ids          : [int]         : List of the job created with this pipeline
            - path              : str           : Path to the pipeline on the server (internal usage only)
            - manifest          : json          : The manifest of the pipeline with all its informations
            - documents         : json          : The dic of the related documents <key>: <path_to_the_doc>. Keys are: manifest, form, icon, help, home, license, readme
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - image_file        : File          : The file of the pipeline image (if exists)
            - jobs              : [Jobs]        : The list of jobs done with this pipeline
    """
    from core.model.file import File
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    # Avoid recursion infinit loop
    if hasattr(self, "loading_depth") and not force_refresh and self.loading_depth >= loading_depth:
        return
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        self.jobs_ids = []
        
        self.jobs = []
        self.image_file = None
        self.jobs_ids = self.get_jobs_ids()
        if self.loading_depth > 0:
            self.jobs = self.get_jobs(self.loading_depth-1)
            self.image_file = File.from_id(self.image_file_id, self.loading_depth-1)
    except Exception as ex:
        raise RegovarException("Pipeline data corrupted (id={}).".format(self.id), "", ex)
            


def pipeline_from_id(pipeline_id, loading_depth=0):
    """
        Retrieve pipeline with the provided id in the database
    """
    pipeline = Session().query(Pipeline).filter_by(id=pipeline_id).first()
    if pipeline:
        Session().refresh(pipeline)
        pipeline.init(loading_depth)
    return pipeline


def pipeline_from_ids(pipeline_ids, loading_depth=0):
    """
        Retrieve pipelines corresponding to the list of provided id
    """
    pipelines = []
    if pipeline_ids and len(pipeline_ids) > 0:
        pipelines = Session().query(Pipeline).filter(Pipeline.id.in_(pipeline_ids)).all()
        for p in pipelines:
            Session().refresh(p)
            p.init(loading_depth)
    return pipelines


def pipeline_to_json(self, fields=None, loading_depth=-1):
    """
        Export the pipeline into json format with only requested fields
    """
    result = {}
    if loading_depth < 0:
        loading_depth = self.loading_depth
    if fields is None:
        fields = ["id", "name", "type", "status", "description", "developpers", "installation_date", "version", "version_api", "image_file_id", "manifest", "documents"]
    for f in fields:
        if f == "installation_date":
            result.update({f: eval("self." + f + ".isoformat()")})
        elif f == "jobs":
            if self.jobs and self.loading_depth > 0:
                result.update({"jobs" : [j.to_json(None, loading_depth-1) for j in self.jobs]})
        elif f == "image_file" and self.image_file:
            result.update({f: self.image_file.to_json(None, loading_depth-1)})
        else:
            result.update({f: eval("self." + f)})
    return result


def pipeline_load(self, data):
    from core.model.file import File
    try:
        # Required fields
        if "name" in data.keys(): self.name = check_string(data['name'])
        if "type" in data.keys(): self.type = check_string(data["type"])
        if "status" in data.keys(): self.status = check_string(data["status"])
        if "description" in data.keys(): self.description = check_string(data["description"])
        if "developpers" in data.keys(): self.developpers = data["developpers"]
        if "installation_date" in data.keys(): self.installation_date = check_date(data["installation_date"])
        if "version" in data.keys(): self.version = check_string(data['version'])
        if "version_api" in data.keys(): self.version_api = check_string(data["version_api"])
        if "image_file_id" in data.keys(): self.image_file_id = check_int(data["image_file_id"])
        if "manifest" in data.keys(): self.manifest = data['manifest']
        if "documents" in data.keys(): self.documents = data['documents']
        if "path" in data.keys(): self.path = check_string(data['path'])
        
        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.jobs = self.get_jobs(self.loading_depth-1)
            self.image_file = File.from_id(self.image_file_id, self.loading_depth-1)
        self.save()
    except KeyError as e:
        raise RegovarException('Invalid input pipeline: missing ' + e.args[0])
    return self


def pipeline_delete(pipeline_id):
    """
        Delete the pipeline with the provided id in the database
    """
    try:
        Session().query(Pipeline).filter_by(id=pipeline_id).delete(synchronize_session=False)
        Session().commit()
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


def pipeline_get_jobs(self, loading_depth=0):
    """
        Return the list of jobs that used the pipeline
    """
    from core.model.job import Job
    jobs = Session().query(Job).filter_by(pipeline_id=self.id)
    result = []
    for j in jobs: 
        Session().refresh(j)
        j.init(loading_depth)
        result.append(j)
    return result


def pipeline_get_jobs_ids(self, loading_depth=0):
    """
        Return the list of jobs ids that used the pipeline
    """
    return [row.id for row in execute("SELECT id FROM job WHERE pipeline_id={0} ORDER BY id DESC".format(self.id))]


Pipeline = Base.classes.pipeline
Pipeline.public_fields = ["id", "name", "type", "status", "description", "developpers", "installation_date", "version", "version_api", "image_file_id", "image_file", "manifest", "documents", "path", "jobs_ids", "jobs"]
Pipeline.init = pipeline_init
Pipeline.from_id = pipeline_from_id
Pipeline.from_ids = pipeline_from_ids
Pipeline.to_json = pipeline_to_json
Pipeline.load = pipeline_load
Pipeline.save = generic_save
Pipeline.delete = pipeline_delete
Pipeline.new = pipeline_new
Pipeline.count = pipeline_count 
Pipeline.get_jobs = pipeline_get_jobs
Pipeline.get_jobs_ids = pipeline_get_jobs_ids
