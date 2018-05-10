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
        # Setting up the lxc container for the job
        docker_container = os.path.basename(job.path)
        manifest = job.pipeline.manifest if isinstance(job.pipeline.manifest, dict) else yaml.load(job.pipeline.manifest)
        docker_job_cmd = manifest["job"]
        docker_logs_path = manifest["logs"]
        docker_inputs_path = manifest["inputs"]
        docker_outputs_path = manifest["outputs"]
        docker_db_path = manifest["databases"]
        docker_image = manifest["image_alias"]
        notify_url = NOTIFY_URL.format(job.id)
        inputs_path = os.path.join(job.path, "inputs")
        outputs_path = os.path.join(job.path, "outputs")
        logs_path = os.path.join(job.path, "logs")
        try:
            # create job's start command file
            job_file = os.path.join(job.path, "start_" + docker_container + ".sh")
            log(job_file)
            with open(job_file, 'w') as f:
                f.write("#!/bin/bash\n")
                if auto_notify:
                    f.write("curl -X POST -d '{{\"status\" : \"running\"}}' {}\n".format(notify_url))
                else:
                    job.status = "running"
                    job.save()

                # TODO : catch if execution return error and notify pirus with error status
                f.write("chmod +x {}\n".format(docker_job_cmd)) # ensure that we can execute the job's script
                f.write("{} 1> {} 2> {}".format(docker_job_cmd, os.path.join(docker_logs_path, 'out.log'), os.path.join(docker_logs_path, "err.log\n"))) #  || curl -X POST -d '{\"status\" : \"error\"}' " + notify_url + "
                f.write("chown -Rf {}:{} {}\n".format(DOCKER_CONFIG["pirus_uid"], DOCKER_CONFIG["pirus_gid"], docker_outputs_path))
                if auto_notify:
                    f.write("curl -X POST -d '{{\"status\" : \"finalizing\"}}' {}\n".format(notify_url))
                os.chmod(job_file, 0o777)
            # create container
            exec_cmd(["lxc", "init", docker_image, docker_container])
            # set up env
            exec_cmd(["lxc", "config", "set", docker_container, "environment.PIRUS_NOTIFY_URL", notify_url ])
            exec_cmd(["lxc", "config", "set", docker_container, "environment.PIRUS_CONFIG_FILE", os.path.join(docker_inputs_path, "config.json") ])
            # Add write access to the container root user to the logsoutputs folders on the host
            exec_cmd(["setfacl", "-Rm", "user:lxd:rwx,default:user:lxd:rwx,user:{0}:rwx,default:user:{0}:rwx".format(DOCKER_CONFIG["docker_uid"]), logs_path])
            exec_cmd(["setfacl", "-Rm", "user:lxd:rwx,default:user:lxd:rwx,user:{0}:rwx,default:user:{0}:rwx".format(DOCKER_CONFIG["docker_uid"]), outputs_path])
            # set up devices
            exec_cmd(["lxc", "config", "device", "add", docker_container, "pirus_inputs",  "disk", "source=" + inputs_path,   "path=" + docker_inputs_path[1:], "readonly=True"])
            exec_cmd(["lxc", "config", "device", "add", docker_container, "pirus_outputs", "disk", "source=" + outputs_path,  "path=" + docker_outputs_path[1:]])
            exec_cmd(["lxc", "config", "device", "add", docker_container, "pirus_logs",    "disk", "source=" + logs_path,     "path=" + docker_logs_path[1:]])
            exec_cmd(["lxc", "config", "device", "add", docker_container, "pirus_db",      "disk", "source=" + DATABASES_DIR, "path=" + docker_db_path[1:], "readonly=True"])
        except Exception as ex:
            raise RegovarException("Unexpected error.", "", ex)

        # Execute the "job" command to start the pipe
        try:
            exec_cmd(["lxc", "start", docker_container])
            docker_job_file = os.path.join("/", os.path.basename(job_file))
            exec_cmd(["lxc", "file", "push", job_file, docker_container + docker_job_file])

            cmd = ["lxc", "exec", "--mode=non-interactive", docker_container, "--",  "chmod", "+x", docker_job_file]
            r, o, e = exec_cmd(cmd)

            cmd = ["lxc", "exec", "--mode=non-interactive", docker_container, "--", docker_job_file]
            exec_cmd(cmd, True)
            # TODO : keep future callback and catch error if start command failled

            # if not asynch:
            #     r, o, e = exec_cmd(cmd)
            #     if e.startswith("error: Container is not running."): # catch docker error
            #         job.status = "error"
            #         job.save()
            #         err('Error occured when starting the job {} (id={}).\n{}'.format(job.name, job.id, e))
            #     else:
            #         log('New job {} (id={}) start with success.'.format(job.name, job.id))
            # else:
            #     subprocess.Popen(cmd)
            #     return True
        except Exception as ex:
            raise RegovarException("Unexpected error.", "", ex)

        return True

        





    def start_job(self, job):
        """
            (Re)Start the job execution. By unfreezing the 
        """
        if not DOCKER_CONFIG: 
          err("Docker not available. Job cannot be start")
          return None
        # Setting up the lxc container for the job
        docker_container = os.path.basename(job.path)
        r, o, e = exec_cmd(["lxc-start", "-n", docker_container, "-d"])
        if r != 0:
            err("Error occured when trying to start the job {} (id={})".format(docker_container, job.id), "$ lxc-start\nstdout ====\n{}\nstderr ====\n{}".format(o, e))
        return r == 0






    def pause_job(self, job):
        """
            Pause the execution of the job.
        """
        if not DOCKER_CONFIG: 
          err("Docker not available. Job cannot be pause")
          return None
        docker_container = os.path.basename(job.path)
        r, o, e = exec_cmd(["lxc-freeze", "-n", docker_container])
        if r != 0:
            err("Error occured when trying to pause the job {} (id={})".format(docker_container, job.id), "$ lxc-freeze\nstdout ====\n{}\nstderr ====\n{}".format(o, e))
        return r == 0




    def stop_job(self, job):
        """
            Stop the job. The job is canceled and the container is destroyed.
        """
        if not DOCKER_CONFIG: 
          err("Docker not available. Job cannot be stop")
          return None
        docker_container = os.path.basename(job.path)
        r, o, e = exec_cmd(["lxc-destroy", "-n", docker_container, "--force"])
        if r != 0:
            err("Error occured when trying to stop the job {} (id={})".format(docker_container, job.id), "$ lxc-destroy --force\nstdout ====\n{}\nstderr ====\n{}".format(o, e))
        return r == 0



    def monitoring_job(self, job):
        """
            Provide monitoring information about the container (CPU/RAM used, etc)
        """
        if not DOCKER_CONFIG: 
          err("Docker not available. Job cannot be monitored")
          return None
        docker_container = os.path.basename(job.path)
        # Result
        result = {}
        # docker monitoring data
        try:
            # TODO : to be reimplemented with pydocker api when this feature will be available :)

            r, o, e = exec_cmd(["lxc-info", "-n", docker_container])
            if r == 0:
                for l in o.split('\n'):
                    data = l.split(': ')
                    if data[0].strip() in ["Name","Created", "Status", "Processes", "Memory (current)", "Memory (peak)"]:
                        result.update({data[0].strip(): data[1]})
        except Exception as ex:
            err("Error occured when retriving monitoring data for job {} (id={})".format(docker_container, job.id), ex)
        return result



    def finalize_job(self, job):
        """
            IMPLEMENTATION REQUIRED
            Clean temp resources created by the container (log shall be kept), copy outputs file from the container
            to the right place on the server, register them into the database and associates them to the job.
        """
        if not DOCKER_CONFIG: 
          err("Docker not available. Job cannot be finalized")
          return None
        docker_container = os.path.basename(job.path)
        # Stop container and clear resource
        try:
            # Clean outputs
            exec_cmd(["lxc-destroy", "-n", docker_container, "--force"], asynch)
        except Exception as ex:
            err("Error occured when trying to finalize the job {} (id={})".format(docker_container, job.id), ex)
            return False
        return True 





