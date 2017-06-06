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
            - "inputs" property set with inputs files (file id are in inputs_ids property). 
            - "outputs" property set with outputs files (file id are in outputs_ids property). 

        If loading_depth == 0, children objects are not loaded, so source will be set with the id of the project if exists
    """
    self.inputs_ids = []
    self.outputs_ids = []
    self.logs = []
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)

    files = session().query(JobFile).filter_by(project_id=self.id).all()
    project_logs_path = os.path.join(str(self.root_path), "logs")
    if os.path.exists(project_logs_path) :
        self.logs = [MonitoringLog(os.path.join(project_logs_path, logname)) for logname in os.listdir(project_logs_path) if os.path.isfile(os.path.join(project_logs_path, logname))]
    for f in files:
        if f.as_input:
            self.inputs_ids.append(f.file_id)
        else:
            self.outputs_ids.append(f.file_id)
    self.load_depth(loading_depth)
            


def project_container_name(self):
    "{}{}-{}".format(LXD_CONTAINER_PREFIX, project.pipeline_id, project.id)

def project_load_depth(self, loading_depth):
    from core.model.file import File
    from core.model.pipeline import Pipeline
    if loading_depth > 0:
        try:
            self.inputs = []
            self.outputs = []
            self.pipeline = None
            self.pipeline = Pipeline.from_id(self.pipeline_id, loading_depth-1)
            if len(self.inputs_ids) > 0:
                files = session().query(File).filter(File.id.in_(self.inputs_ids)).all()
                for f in files:
                    f.init(loading_depth-1)
                    self.inputs.append(f)
            if len(self.outputs_ids) > 0:
                files = session().query(File).filter(File.id.in_(self.outputs_ids)).all()
                for f in files:
                    f.init(loading_depth-1)
                    self.outputs.append(f)
        except Exception as err:
            raise RegovarException("File data corrupted (id={}).".format(self.id), "", err)





def project_from_id(project_id, loading_depth=0):
    """
        Retrieve project with the provided id in the database
    """
    project = session().query(Job).filter_by(id=project_id).first()
    if project:
        project.init(loading_depth)
    return project


def project_from_ids(project_ids, loading_depth=0):
    """
        Retrieve projects corresponding to the list of provided id
    """
    projects = []
    if project_ids and len(project_ids) > 0:
        projects = session().query(Job).filter(Job.id.in_(project_ids)).all()
        for f in projects:
            f.init(loading_depth)
    return projects


def project_to_json(self, fields=None):
    """
        Export the project into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = ["id", "pipeline_id", "config", "start_date", "update_date", "status", "progress_value", "progress_label", "inputs_ids", "outputs_ids"]
    for f in fields:
        if f == "start_date" or f == "update_date" :
            result.update({f: eval("self." + f + ".ctime()")})
        elif f == "inputs":
            if self.loading_depth == 0:
                result.update({"inputs" : [i.to_json() for i in self.inputs]})
            else:
                result.update({"inputs" : self.inputs})
        elif f == "inputs":
            if self.loading_depth == 0:
                result.update({"outputs" : [o.to_json() for o in self.outputs]})
            else:
                result.update({"outputs" : self.outputs})
        elif f == "config" and self.config:
            result.update({f: json.loads(self.config)})
        else:
            result.update({f: eval("self." + f)})
    return result


def project_load(self, data):
    try:
        # Required fields
        if "name" in data.keys(): self.name = data['name']
        if "pipeline_id" in data.keys(): self.pipeline_id = data['pipeline_id']
        if "config" in data.keys(): self.config = data["config"]
        if "start_date" in data.keys(): self.start_date = int(data["start_date"])
        if "update_date" in data.keys(): self.update_date = int(data["update_date"])
        if "status" in data.keys(): self.status = data["status"]
        if "progress_value" in data.keys(): self.progress_value = data["progress_value"]
        if "progress_label" in data.keys(): self.progress_label = data['progress_label']
        if "inputs_ids" in data.keys(): self.inputs_ids = data["inputs_ids"]
        if "outputs_ids" in data.keys(): self.outputs_ids = data["outputs_ids"]
        self.save()

        # delete old file/project links
        session().query(JobFile).filter_by(project_id=self.id).delete(synchronize_session=False)
        # create new links
        for fid in self.inputs_ids: JobFile.new(self.id, fid, True)
        for fid in self.outputs_ids: JobFile.new(self.id, fid, False)

        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.load_depth(self.loading_depth)
    except KeyError as e:
        raise RegovarException('Invalid input project: missing ' + e.args[0])
    return self


def project_save(self):
    generic_save(self)

    # Todo : save project/files associations
    if hasattr(self, 'inputs') and self.inputs: 
        # clear all associations
        # save new associations
        pass
    if hasattr(self, 'outputs') and self.outputs: 
        # clear all associations
        # save new associations
        pass


def project_delete(project_id):
    """
        Delete the project with the provided id in the database
    """
    session().query(Job).filter_by(id=project_id).delete(synchronize_session=False)
    session().query(JobFile).filter_by(project_id=project_id).delete(synchronize_session=False)


def project_new():
    """
        Create a new project and init/synchronise it with the database
    """
    j = Job()
    j.save()
    j.init()
    return j


def project_count():
    """
        Return total of Job entries in database
    """
    return generic_count(Job)


Job = Base.classes.project
Job.public_fields = ["id", "pipeline_id", "config", "start_date", "update_date", "status", "progress_value", "progress_label", "inputs_ids", "outputs_ids", "inputs", "outputs"]
Job.init = project_init
Job.load_depth = project_load_depth
Job.from_id = project_from_id
Job.from_ids = project_from_ids
Job.to_json = project_to_json
Job.load = project_load
Job.save = project_save
Job.new = project_new
Job.delete = project_delete
Job.count = project_count