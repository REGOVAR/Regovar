#!env/python3
# coding: utf-8
import os
import json


from core.framework.common import *
from core.framework.postgresql import *





# =====================================================================================================================
# Monitoring log wrapper
# =====================================================================================================================
class MonitoringLog:
    """
        Class to wrap log file and provide usefull related information and method to parse logs
    """
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.size = os.path.getsize(path)
        self.creation = datetime.datetime.fromtimestamp(os.path.getctime(path))
        self.update = datetime.datetime.fromtimestamp(os.path.getmtime(path))


    def tail(self, lines_number=100):
        """
            Return the N last lines of the log
        """
        try: 
            log_tail = subprocess.check_output(["tail", self.path, "-n", str(lines_number)]).decode()
        except Exception as ex:
            err("Error occured when getting tail of log {}".format(self.path), ex)
            log_tail = "No stdout log of the run."
        return log_tail

        
    def head(self, lines_number=100):
        """
            Return the N first lines of the log
        """
        try: 
            log_head = subprocess.check_output(["head", self.path, "-n", str(lines_number)]).decode()
        except Exception as ex:
            err("Error occured when getting head of log {}".format(self.path), ex)
            log_head = "No stderr log of the run."
        return log_head


    def snip(self, from_line, to_line):
        """
            Return a snippet of the log, from the line N to the line N2
        """
        # TODO
        pass

    def lines_count(self):
        # TODO
        pass






# =====================================================================================================================
# JOB
# =====================================================================================================================
def job_init(self, loading_depth=0):
    """
        If loading_depth is > 0, children objects will be loaded. Max depth level is 2.
        Children objects of a job are :
            - "inputs" property set with inputs files (file id are in inputs_ids property). 
            - "outputs" property set with outputs files (file id are in outputs_ids property). 

        If loading_depth == 0, children objects are not loaded, so source will be set with the id of the job if exists
    """
    self.inputs_ids = []
    self.outputs_ids = []
    self.logs = []
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)

    files = session().query(JobFile).filter_by(job_id=self.id).all()
    job_logs_path = os.path.join(str(self.path), "logs")
    if os.path.exists(job_logs_path) :
        self.logs = [MonitoringLog(os.path.join(job_logs_path, logname)) for logname in os.listdir(job_logs_path) if os.path.isfile(os.path.join(job_logs_path, logname))]
    for f in files:
        if f.as_input:
            self.inputs_ids.append(f.file_id)
        else:
            self.outputs_ids.append(f.file_id)
    self.load_depth(loading_depth)


def job_load_depth(self, loading_depth):
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
            


def job_container_name(self):
    "{}{}-{}".format(LXD_CONTAINER_PREFIX, job.pipeline_id, job.id)





def job_from_id(job_id, loading_depth=0):
    """
        Retrieve job with the provided id in the database
    """
    job = session().query(Job).filter_by(id=job_id).first()
    if job:
        job.init(loading_depth)
    return job


def job_from_ids(job_ids, loading_depth=0):
    """
        Retrieve jobs corresponding to the list of provided id
    """
    jobs = []
    if job_ids and len(job_ids) > 0:
        jobs = session().query(Job).filter(Job.id.in_(job_ids)).all()
        for f in jobs:
            f.init(loading_depth)
    return jobs


def job_to_json(self, fields=None):
    """
        Export the job into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = ["id", "name", "pipeline_id", "config", "start_date", "update_date", "status", "progress_value", "progress_label", "inputs_ids", "outputs_ids"]
    for f in fields:
        if f == "start_date" or f == "update_date" :
            result.update({f: eval("self." + f + ".isoformat()")})
        elif f == "inputs":
            if self.loading_depth > 0:
                result.update({"inputs" : [i.to_json() for i in self.inputs]})
            else:
                result.update({"inputs" : self.inputs})
        elif f == "outputs":
            if self.loading_depth > 0:
                result.update({"outputs" : [o.to_json() for o in self.outputs]})
            else:
                result.update({"outputs" : self.outputs})
        elif f == "pipeline":
            if self.loading_depth > 0:
                result.update({"pipeline" : self.pipeline.to_json()})
        elif f == "logs":
            logs = []
            for l in self.logs:
                logs.append(l.path)
            result.update({"logs" : logs})
        elif f == "config" and self.config:
            result.update({f: json.loads(self.config)})
        # else
        elif f in Job.public_fields:
            result.update({f: eval("self." + f)})
    return result


def job_load(self, data):
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
        if "path" in data.keys(): self.path = data["path"]
        self.save()

        # delete old file/job links
        session().query(JobFile).filter_by(job_id=self.id).delete(synchronize_session=False)
        # create new links
        for fid in self.inputs_ids: JobFile.new(self.id, fid, True)
        for fid in self.outputs_ids: JobFile.new(self.id, fid, False)

        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.load_depth(self.loading_depth)
    except KeyError as e:
        raise RegovarException('Invalid input job: missing ' + e.args[0])
    return self


def job_save(self):
    generic_save(self)

    # Todo : save job/files associations
    if hasattr(self, 'inputs') and self.inputs: 
        # clear all associations
        # save new associations
        pass
    if hasattr(self, 'outputs') and self.outputs: 
        # clear all associations
        # save new associations
        pass


def job_delete(job_id):
    """
        Delete the job with the provided id in the database
    """
    session().query(Job).filter_by(id=job_id).delete(synchronize_session=False)
    session().query(JobFile).filter_by(job_id=job_id).delete(synchronize_session=False)


def job_new():
    """
        Create a new job and init/synchronise it with the database
    """
    j = Job()
    j.save()
    j.init()
    return j


def job_count():
    """
        Return total of Job entries in database
    """
    return generic_count(Job)


Job = Base.classes.job
Job.public_fields = ["id", "pipeline_id", "pipeline", "config", "start_date", "update_date", "status", "progress_value", "progress_label", "inputs_ids", "outputs_ids", "inputs", "outputs", "path", "logs", "name"]
Job.init = job_init
Job.load_depth = job_load_depth
Job.from_id = job_from_id
Job.from_ids = job_from_ids
Job.to_json = job_to_json
Job.load = job_load
Job.save = job_save
Job.new = job_new
Job.delete = job_delete
Job.count = job_count








# =====================================================================================================================
# JOBFILE associations
# =====================================================================================================================



def jobfile_get_jobs(file_id, loading_depth=0):
    """
        Return the list of jobs that are using the file (as input and/or output)
    """
    result = jobs = []
    jobs_ids = jobfile_get_jobs_ids(file_id)
    if len(jobs_ids) > 0:
        jobs = session().query(Job).filter(Job.id.in_(jobs_ids)).all()
    for j in jobs:
        j.init(loading_depth)
        result.append(j)
    return result


def jobfile_get_inputs(job_id, loading_depth=0):
    """
        Return the list of input's files of the job
    """
    result = files = []
    files_ids = jobfile_get_inputs_ids(job_id)
    if len(files) > 0:
        files = session().query(File).filter(File.id.in_(files_ids)).all()
    for f in files:
        f.init(loading_depth)
        result.append(f)
    return result


def jobfile_get_outputs(job_id, loading_depth=0):
    """
        Return the list of output's files of the job
    """
    result = files = []
    files_ids = jobfile_get_outputs_ids(job_id)
    if len(files) > 0:
        files = session().query(File).filter(File.id.in_(files_ids)).all()
    for f in files:
        f.init(loading_depth)
        result.append(f)
    return result


def jobfile_get_jobs_ids(file_id):
    """
        Return the list of job's id that are using the file (as input and/or output)
    """
    result = []
    jobs = session().query(JobFile).filter_by(file_id=file_id).all()
    for j in jobs:
        result.append(j.job_id)
    return result
    

def jobfile_get_inputs_ids(job_id):
    """
        Return the list of file's id that are used as input for the job
    """
    result = []
    files = session().query(JobFile).filter_by(job_id=job_id, as_input=True).all()
    for f in files:
        result.append(f.file_id)
    return result


def jobfile_get_outputs_ids(job_id):
    """
        Return the list of file's id that are used as output for the job
    """
    result = []
    files = session().query(JobFile).filter_by(job_id=job_id, as_input=False).all()
    for f in files:
        result.append(f.file_id)
    return result


def jobfile_new(job_id, file_id, as_input=False):
    """
        Create a new job-file association and save it in the database
    """
    jf = JobFile(job_id=job_id, file_id=file_id, as_input=as_input)
    jf.save()
    return jf

JobFile = Base.classes.job_file
JobFile.get_jobs = jobfile_get_jobs
JobFile.get_inputs = jobfile_get_inputs
JobFile.get_outputs = jobfile_get_outputs
JobFile.get_jobs_ids = jobfile_get_jobs_ids
JobFile.get_inputs_ids = jobfile_get_inputs_ids
JobFile.get_outputs_ids = jobfile_get_outputs_ids
JobFile.save = generic_save
JobFile.new = jobfile_new
 
