 #!env/python3
# coding: utf-8
import ipdb

import os
import shutil
import json
import tarfile
import datetime
import time
import uuid
import subprocess
import requests



from config import *
from core.framework.common import *
from core.model import *




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Job MANAGER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class JobManager:
    def __init__(self):
        pass



    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
        """
            Generic method to get jobs according provided filtering options
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {}
        if order is None:
            order = "name"
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        s = session()
        jobs = s.query(Job).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for j in jobs: j.init(depth)
        return jobs



    def new(self, pipeline_id:int, name:str, config:dict, inputs_ids=[], asynch=True, auto_notify=True):
        """
            Create a new job for the specified pipepline (pipeline_id), with provided config and input's files ids
        """
        pipeline = Pipeline.from_id(pipeline_id)
        if not pipeline : 
            raise RegovarException("Pipeline not found (id={}).".format(pipeline_id))
        if pipeline.status != "ready":
            raise RegovarException("Pipeline status ({}) is not \"ready\". Cannot create a job.".format(pipeline.status))
        if not name:
            raise RegovarException("A name must be provided to create new job")
        # Init model
        job = Job.new()
        job.status = "initializing"
        job.name = name
        job.config = json.dumps(config, sort_keys=True, indent=4)
        job.progress_value = 0
        job.pipeline_id = pipeline_id
        job.progress_label = "0%"
        for fid in inputs_ids: JobFile.new(job.id, int(fid), True)
        job.save()
        # TODO : check if enough free resources to start the new job. otherwise, set status to waiting and return
        job.init(1, True)
        # Init directories entries for the container
        job.path = os.path.join(JOBS_DIR, CONTAINERS_CONFIG[job.pipeline.type]["job_name"].format("{}-{}".format(job.pipeline_id, job.id)))
        job.save()
        inputs_path = os.path.join(job.path, "inputs")
        outputs_path = os.path.join(job.path, "outputs")
        logs_path = os.path.join(job.path, "logs")
        if not os.path.exists(inputs_path): 
            os.makedirs(inputs_path)
        if not os.path.exists(outputs_path):
            os.makedirs(outputs_path)
            os.chmod(outputs_path, 0o777)
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
            os.chmod(logs_path, 0o777)
        
        # Set job's config in the inputs directory of the job
        config_path = os.path.join(inputs_path, "config.json")
        job_config = {
            "pirus" : {"notify_url" : NOTIFY_URL.format(job.id), "job_name" : job.name},
            "job" : config
        }
        with open(config_path, 'w') as f:
            f.write(json.dumps(job_config, sort_keys=True, indent=4))
            os.chmod(config_path, 0o777)

        # Check that all inputs files are ready to be used
        for f in job.inputs:
            if f is None :
                self.set_status(job, "error", asynch=asynch)
                raise RegovarException("Inputs file deleted before the start of the job {} (id={}). Job aborded.".format(job.name, job.id))
            if f.status not in ["checked", "uploaded"]:
                # inputs not ready, we keep the run in the waiting status
                war("INPUTS of the run not ready. waiting")
                self.set_status(job, "waiting", asynch=asynch)
                return Job.from_id(job.id)
        for f in job.inputs:
            link_path = os.path.join(inputs_path, f.name)
            os.link(f.path, link_path)
            os.chmod(link_path, 0o644)

        # Call init of the container
        # if asynch: 
        #     print("run init async")
        #     run_async(self.__init_job, job.id, asynch, auto_notify)
        # else:
        #     print("run init")
        self.__init_job(job.id, asynch, auto_notify)

        # Return job object
        return Job.from_id(job.id)



    def start(self, job_id, asynch=True):
        """
            Start or restart the job
        """
        job = Job.from_id(job_id)
        if not job:
            raise RegovarException("Job not found (id={}).".format(job_id))
        # If job is still initializing
        if job.status == "initializing":
            if asynch: 
                run_async(self.__init_job, (job.id, asynch, True))
                return True
            else:
                return self.__init_job(job.id, asynch, True)

        if job.status not in ["waiting", "pause"]:
            raise RegovarException("Job status ({}) is not \"pause\" or \"waiting\". Cannot start the job.".format(job.status))
        # Call start of the container
        if asynch: 
            run_async(self.__start_job, (job.id, asynch,))
            return True
        else:
            return self.__start_job(job.id, asynch)


    def monitoring(self, job_id):
        """
            Retrieve monitoring information about the job.
            Return a Job object with a new attribute:
             - logs : list of MonitoringLog (log file) write by the run/manager in the run's logs directory
        """
        from core.core import core
        job = Job.from_id(job_id, 1)
        if not job:
            raise RegovarException("Job not found (id={}).".format(job_id))
        if job.status == "initializing":
            raise RegovarException("Job status is \"initializing\". Cannot retrieve yet monitoring informations.")
        # Ask container manager to update data about container
        try:
            job.logs_moninitoring = core.container_managers[job.pipeline.type].monitoring_job(job)
        except Exception as ex:
            err("Error occured when retrieving monitoring information for the job {} (id={})".format(os.path.basename(job.path), job.id), ex)
        return job



    def pause(self, job_id, asynch=True):
        """
            Pause the job
            Return False if job cannot be pause; True otherwise
        """
        from core.core import core

        job = Job.from_id(job_id, 1)
        if not job:
            raise RegovarException("Job not found (id={}).".format(job_id))
        if not job.pipeline:
            raise RegovarException("No Pipeline associated to this job.")
        if not job.pipeline.type:
            raise RegovarException("Type of pipeline for this job is not set.")
        if job.pipeline.type not in core.container_managers.keys():
            raise RegovarException("Pipeline type of this job is not managed.")
        if not core.container_managers[job.pipeline.type].supported_features["pause_job"]:
            return False
        # Call pause of the container
        if asynch: 
            run_async(self.__pause_job, (job.id, asynch,))
            return True
        else:
            return self.__pause_job(job.id, asynch)




    def stop(self, job_id, asynch=True):
        """
            Stop the job
        """
        job = Job.from_id(job_id)
        if not job:
            raise RegovarException("Job not found (id={}).".format(job_id))
        if job.status in ["error", "canceled", "done"]:
            raise RegovarException("Job status is \"{}\". Cannot stop the job.".format(job.status))
        # Call stop of the container
        if asynch: 
            run_async(self.__stop_job, (job.id, asynch,))
            return True
        else:
            return self.__stop_job(job.id, asynch)



    def finalize(self, job_id, asynch=True):
        """
            Shall be called by the job itself when ending.
            save outputs files and ask the container manager to delete container
        """
        from core.core import core

        job = Job.from_id(job_id)
        if not job:
            raise RegovarException("Job not found (id={}).".format(job_id))
        if job.status in ["canceled", "done", "error"]:
            raise RegovarException("Job status is \"{}\". Cannot be finalized.".format(job.status))
        # Register outputs files
        outputs_path = os.path.join(job.path, "outputs")
        logs_path = os.path.join(job.path, "logs")
        for f in os.listdir(outputs_path):
            file_path = os.path.join(outputs_path, f)
            if os.path.isfile(file_path):
                # 1- Move & store file into Pirus DB/Filesystem
                pf = core.files.from_local(file_path, True, {"job_source_id" : job.id})
                # 2- create link (to help admins when browsing pirus filesystem)
                os.link(pf.path, file_path)
                # 3- update job's entry in db to link file to job's outputs
                JobFile.new(job_id, pf.id)
        # Stop container and delete it
        if asynch: 
            run_async(self.__finalize_job, (job.id, asynch,))
            return True
        else:
            return self.__finalize_job(job.id, asynch)



    def delete(self, job_id, asynch=True):
        """
            Delete a Job. Outputs that have not yet been saved in Pirus, will be deleted.
        """
        job = Job.from_id(job_id, 1)
        if not job:
            raise RegovarException("Job not found (id={}).".format(job_id))
        # Security, force call stop/delete the container
        if asynch: 
            run_async(self.__finalize_job, (job.id, asynch,))
        else:
            self.__finalize_job(job.id, asynch)
        # Deleting file in the filesystem
        shutil.rmtree(job.path, True)
        return job




    def set_status(self, job, new_status, notify=True, asynch=True):
        from core.core import core
        # Avoid useless notification
        # Impossible to change state of a job in error or canceled
        if (new_status != "running" and job.status == new_status) or job.status in  ["error", "canceled"]:
            return
        # Update status
        job.status = new_status
        job.save()

        # Need to do something according to the new status ?
        # Nothing to do for status : "waiting", "initializing", "running", "finalizing"
        if job.status in ["pause", "error", "done", "canceled"]:
            s = session()
            next_jobs = s.query(Job).filter_by(status="waiting").order_by("priority").all()
            if len(next_jobs) > 0:
                if asynch: 
                    run_async(self.start, (next_jobs[0].id, asynch,))
                else:
                    self.start(next_jobs[0].id, asynch)
        elif job.status == "finalizing":
            # if asynch: 
            #     run_async(self.finalize, (job.id, asynch,))
            # else:
            self.finalize(job.id, asynch)
        # Push notification
        if notify:
            core.notify_all(data={"action": "job_updated", "data" : [job.to_json()]})


    def __init_job(self, job_id, asynch, auto_notify):
        """
            Call manager to prepare the container for the job.
        """
        from core.core import core

        job = Job.from_id(job_id, 1)
        if job and job.status == "initializing":
            try:
                success = core.container_managers[job.pipeline.type].init_job(job, asynch, auto_notify)
            except Exception as ex:
                # TODO : Manage error
                self.set_status(job, "error", asynch)
                return False
            self.set_status(job, "running" if success else "error", asynch) 
            return True
        err("Job initializing already done or failled. Not able to reinitialise it.")
        return False



    def __start_job(self, job_id, asynch):
        """
            Call the container manager to start or restart the execution of the job.
        """
        from core.core import core

        # Check that job exists
        job = Job.from_id(job_id, 1)
        if not job :
            # TODO : log error
            return False

        # Ok, job is now waiting
        self.set_status(job, "waiting")

        # Check that all inputs files are ready to be used
        for file in job.inputs:
            if file is None :
                err("Inputs file deleted before the start of the job {} (id={}). Job aborded.".format(job.name, job.id))
                self.set_status(job, "error", asynch=asynch)
                return False
            if file.status not in ["checked", "uploaded"]:
                # inputs not ready, we keep the run in the waiting status
                war("INPUTS of the run not ready. waiting")
                self.set_status(job, "waiting", asynch=asynch)
                return False
            
        # TODO : check that enough reszources to run the job
        # Inputs files ready to use, looking for lxd resources now
        # count = 0
        # for lxd_container in lxd_client.containers.all():
        #     if lxd_container.name.startswith(LXD_CONTAINER_PREFIX) and lxd_container.status == 'Running':
        #         count += 1
        # count = len(Run.objects(status="RUNNING")) + len(Run.objects(status="INITIALIZING")) + len(Run.objects(status="FINISHING"))
        # if len(Run.objects(status="RUNNING")) >= LXD_MAX:
        #     # too many run in progress, we keep the run in the waiting status
        #     print("To many run in progress, we keep the run in the waiting status")
        #     return 1

        #Try to run the job
        if core.container_managers[job.pipeline.type].start_job(job):
            self.set_status(job, "running", asynch)
            return True
        return False





    def __pause_job(self, job_id, asynch):
        """
            Call manager to suspend the execution of the job.
        """
        from core.core import core

        job = Job.from_id(job_id, 1)
        if job:
            try:
                core.container_managers[job.pipeline.type].pause_job(job)
            except Exception as ex:
                # TODO : Log error
                self.set_status(job, "error", asynch)
                return False
            self.set_status(job, "pause", asynch)
            return True
        return False


    def __stop_job(self, job_id, asynch):
        """
            Call manager to stop execution of the job.
        """
        from core.core import core

        job = Job.from_id(job_id, 1)
        if job:
            try:
                core.container_managers[job.pipeline.type].stop_job(job)
            except Exception as ex:
                # Log error
                self.set_status(job, "error", asynch)
                return False
            self.set_status(job, "canceled", asynch)
            return True
        return False



    def __finalize_job(self, job_id, asynch):
        """
            Ask the manager to clear the container
        """
        from core.core import core
        
        job = Job.from_id(job_id, 1)
        if not job :
            # TODO : log error
            return 

        if core.container_managers[job.pipeline.type].finalize_job(job):
            self.set_status(job, "done", asynch)
            return True
        else:
            self.set_status(job, "error", asynch)
            return False
        return False
