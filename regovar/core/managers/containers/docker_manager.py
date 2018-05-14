#!env/python3
# coding: utf-8
import ipdb
import os
import uuid
import json
import yaml
import tarfile
import subprocess
import shutil
import docker

from config import *
from core.framework.common import *

from core.managers.containers.abstract_container_manager import AbstractContainerManager
from core.model import *




def waiting_container(job_id):
    """
        This method wait for the end of the execution of the container in another
        thread (to not block the main application) and update job status accordingly)
    """
    from core.core import core
    from core.model import Job
    job = Job.from_id(job_id)
    container_name = DOCKER_CONFIG["job_name"].format("{}_{}".format(job.pipeline_id, job.id))
    
    try:
        container = docker.from_env().containers.get(container_name)
    except Exception as ex:
        pass
    
    # wait until the container stops
    container.wait()
    
    # refresh job information
    job = Job.from_id(job_id, 1)
    if job.status == 'running':
        # The container stop auto when its job is done, so have to finalyse it
        core.jobs.finalize(job_id)
    # else:
    # The container have been stop by someone else (pause, stop, admin...)
    # do nothing
        
        
        


class DockerManager(AbstractContainerManager):
    """
        Pirus manager to run pipeline from Docker container
    """
    
    def __init__(self):
        # Job's control features supported by this bind of pipeline
        self.supported_features = {
            "pause_job" : True,
            "stop_job" : True,
            "monitoring_job" : True
        }
        try:
            self.docker = docker.from_env()
        except ex:
            self.docker = None
            raise RegovarException("Docker not available.", exception=ex)


        # Check list of docker container. 
        # TODO: finalyse all regovar's containers that are in "exited" status


    def install_pipeline(self, pipeline):
        """
            Perform the installation of a pipeline that use Docker container
        """
        if not self.docker: 
          err("Docker not available. Pipeline installation abord")
          return None
        if not pipeline or not isinstance(pipeline, Pipeline) :
            raise RegovarException("Pipeline's data error.")
        pipeline.init(1)
        if not pipeline.image_file or not pipeline.image_file.path:
            raise RegovarException("Pipeline image file's data error.")

        root_path = os.path.join(PIPELINES_DIR, str(pipeline.id))
        manifest = pipeline.manifest
        

        # 2- Save checked manifest/config into database
        image_alias = DOCKER_CONFIG["image_name"].format(pipeline.id)
        manifest["image_alias"] = image_alias
        pipeline.load(manifest)
        pipeline.manifest = manifest
        pipeline.path = root_path
        
        try:
            pipeline.save()
        except Exception as ex:
            raise RegovarException("FAILLED to save the new pipeline in database (already exists or wrong name ?).", "", ex)
        log("Pipeline saved in database with id={}".format(pipeline.id))

        # 3- Install docker container
        image = self.docker.images.build(path=pipeline.path, tag=image_alias)

        log("Docker image {} created. Pipeline is ready".format(image_alias))
        pipeline.status = "ready"
        pipeline.save()
        return pipeline




    def uninstall_pipeline(self, pipeline):
        """
            Uninstall the pipeline docker image.
            Database & filesystem clean is done by the core
        """
        if not self.docker: 
          err("Docker not available. Pipeline uninstallation abord")
          return None
        if not pipeline or not isinstance(pipeline, Pipeline) :
            raise RegovarException("Pipeline's data error.")
        # Retrieve container settings
        manifest = pipeline.manifest
        image_alias = manifest["image_alias"]
        # Uninstall docker container
        try:
            self.docker.images.remove(image_alias, force=True)
        except Exception as ex:
            raise RegovarException("FAILLED Removing the docker image {}.".format(image_alias), exception=ex)







        



    def init_job(self, job, auto_notify=True):
        """
            Init a job :
            - check settings (stored in database) 
            - create the docker container from pipeline image
            - configure container and mount I/O directories to the filesystem

            auto_notify : tell the container to send 2 notifications :
                          the first one before starting to update status to "running"
                          the last one at the end of the job to update status to "finalizing"
                          if set to false, you will have to monitore yourself the execution of the job
                          to finalize it when its done.
        """
        if not self.docker: 
            err("Docker not available. Job init abord")
            return None
      
        docker_container = os.path.basename(job.path)
      
        try:
            container = self.docker.containers.get(docker_container)
            err("Job container '{}' already exists, abord init.".format(docker_container))
            return None
        except Exception as ex:
            pass
      
        # Setting up the docker container for the job
        manifest = job.pipeline.manifest if isinstance(job.pipeline.manifest, dict) else yaml.load(job.pipeline.manifest)
        docker_logs_path = manifest["logs"]
        docker_inputs_path = manifest["inputs"]
        docker_outputs_path = manifest["outputs"]
        docker_db_path = manifest["databases"]
        docker_image = manifest["image_alias"]
        notify_url = NOTIFY_URL.format(job.id)
        inputs_path = os.path.join(job.path, "inputs")
        outputs_path = os.path.join(job.path, "outputs")
        logs_path = os.path.join(job.path, "logs")
        env = ["NOTIFY_URL={}".format(notify_url)]
        try:
            container = self.docker.containers.run(
                docker_image,
                environment = env,
                name = docker_container,
                network = DOCKER_CONFIG["network"],
                user = DOCKER_CONFIG["user_mapping"],
                volumes = {
                    inputs_path: {'bind': docker_inputs_path, 'mode': 'ro'},
                    DATABASES_DIR: {'bind': docker_db_path, 'mode': 'ro'},
                    outputs_path: {'bind': docker_outputs_path, 'mode': 'rw'},
                    logs_path: {'bind': logs_path, 'mode': 'rw'},
                    },
                detach = True)
        except Exception as ex:
            raise RegovarException("Error when trying to run the container {} with docker.".format(docker_container), exception=ex)

        run_async(waiting_container, job.id)

        return True

        





    def start_job(self, job):
        """
            Start the job into the container. The container may already exists as this method can be call
            after init_job and pause_job.
            Return True if success; False otherwise
        """
        docker_container = os.path.basename(job.path)
        try:
            container = self.docker.containers.get(docker_container)
        except Exception as ex:
            err("Job container '{}' do not exists, abord start operation.".format(docker_container))
            return False
        try:
            if container.status == "paused":
                container.unpause()
                run_async(waiting_container, job.id)
            elif container.status == "exited":
                container.start()
                run_async(waiting_container, job.id)
            else:
                err("Job container '{}' status do not allow start operation.".format(docker_container))
                return False
        except Exception as ex:
            raise RegovarException("Error occured when trying to (re)start the docker container '{}'.".format(docker_container), exception=ex)
        return True





    def pause_job(self, job):
        """
            Pause the execution of the job to save server resources by example
            Return True if success; False otherwise
        """
        docker_container = os.path.basename(job.path)
        try:
            container = self.docker.containers.get(docker_container)
        except Exception as ex:
            err("Job container '{}' do not exists, abord start operation.".format(docker_container))
            return False
        try:
            if container.status == "running":
                container.pause()
            else:
                err("Job container '{}' status do not allow pause operation.".format(docker_container))
                return False
        except Exception as ex:
            raise RegovarException("Error occured when trying to pause the docker container '{}'.".format(docker_container), exception=ex)
        return True




    def stop_job(self, job):
        """
            Stop the job. The job is canceled and the container shall be destroyed
            Return True if success; False otherwise
        """
        docker_container = os.path.basename(job.path)
        try:
            container = self.docker.containers.get(docker_container)
        except Exception as ex:
            err("Job container '{}' do not exists, abord stop operation.".format(docker_container))
            return False
        try:
            container.remove(force=True, v=False)
        except Exception as ex:
            raise RegovarException("Error occured when trying to remove the docker container '{}'.".format(docker_container), exception=ex)
        return True
    
    


    def list_jobs(self, job):
        """
            Return list of all job (running or paused)
        """
        if self.supported_features["monitoring_job"]:
            raise RegovarException("The abstract method \"monitoring_job\" of PirusManager shall be implemented.")





    def monitoring_job(self, job):
        """
            Provide monitoring information about the container (CPU/RAM used, update logs files if needed, etc)
            Return monitoring information as json; None otherwise
        """
        docker_container = os.path.basename(job.path)
        try:
            container = self.docker.containers.get(docker_container)
        except Exception as ex:
            err("Job container '{}' do not exists, abord stop operation.".format(docker_container))
            return False
        
        try:
            manifest = job.pipeline.manifest if isinstance(job.pipeline.manifest, dict) else yaml.load(job.pipeline.manifest)
            docker_logs_path = manifest["logs"]
            # Refresh logs files out & err
            with open(os.path.join(docker_logs_path, "out.log"), "w") as f:
                f.write(container.logs(stdout=True, stderr=False))
            with open(os.path.join(docker_logs_path, "err.log"), "w") as f:
                f.write(container.logs(stdout=False, stderr=True))
            # Get docker stats
            stats = container.stats(stream=False)
            stats["status"] = container.status
            
        except Exception as ex:
            raise RegovarException("Error occured when trying to remove the docker container '{}'.".format(docker_container), exception=ex)
        
        return stats
    




    def finalize_job(self, job):
        """
            Clean temp resources created by the container (log shall be kept)
            Return True if success; False otherwise
        """
        print("==== > finalize_job")
        docker_container = os.path.basename(job.path)
        try:
            container = self.docker.containers.get(docker_container)
        except Exception as ex:
            err("Job container '{}' do not exists, abord stop operation.".format(docker_container))
            return False
        try:
            container.remove(force=True, v=False)
        except Exception as ex:
            raise RegovarException("Error occured when trying to remove the docker container '{}'.".format(docker_container), exception=ex)
        return True






