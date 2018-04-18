#!env/python3
# coding: utf-8
import ipdb
import os
import uuid
import json
import yaml
import tarfile
import ipdb
import subprocess
import shutil

from config import *
from core.framework.common import *

from core.managers.containers.abstract_container_manager import AbstractContainerManager
from core.model import *




class LxdManager(AbstractContainerManager):
    """
        Pirus manager to run pipeline from LXD container
    """
    def __init__(self):
        # To allow the core to know if this kind of pipeline need an image to be donwloaded for the installation
        self.need_image_file = True
        # Job's control features supported by this bind of pipeline
        self.supported_features = {
            "pause_job" : True,
            "stop_job" : True,
            "monitoring_job" : True
        }

        if not CONTAINERS_CONFIG or "lxd" not in CONTAINERS_CONFIG.keys() or not CONTAINERS_CONFIG["lxd"]:
            raise RegovarException("No configuration settings found for lxd")
        self.config = CONTAINERS_CONFIG["lxd"]



    def install_pipeline(self, pipeline, asynch=False):
        """
            Perform the installation of a pipeline that use LXD container
        """
        if not pipeline or not isinstance(pipeline, Pipeline) :
            raise RegovarException("Pipeline's data error.")
        pipeline.init(1)
        if not pipeline.image_file or not pipeline.image_file.path:
            raise RegovarException("Pipeline image file's data error.")
        root_path = os.path.join(PIPELINES_DIR, str(pipeline.id))

        # 0- retrieve conf related to LXD
        if not CONTAINERS_CONFIG or "lxd" not in CONTAINERS_CONFIG.keys() or not CONTAINERS_CONFIG["lxd"]:
            raise RegovarException("No configuration settings found for lxd")
        conf = CONTAINERS_CONFIG["lxd"]
        
        # 1- Check that mandatory fields exists
        manifest = pipeline.manifest
        missing = ""
        for k in conf["manifest"]["mandatory"].keys():
            if k not in manifest.keys():
                missing += k + ", "                
        if missing != "":
            missing = missing[:-2]
            raise RegovarException("FAILLED Checking validity of manifest (missing : {})".format(missing))
        log('Validity of manifest checked')

        # 2- Default value for optional fields in mandatory file
        for k in conf["manifest"]["default"].keys():
            if k not in manifest.keys():
                manifest[k] = conf["manifest"]["default"][k]

        # 3- Save checked manifest/config into database
        lxd_alias = conf["image_name"].format(pipeline.id)
        manifest["lxd_alias"] = lxd_alias
        pipeline.load(manifest)
        pipeline.manifest = manifest
        pipeline.path = root_path
        
        try:
            pipeline.save()
        except Exception as ex:
            raise RegovarException("FAILLED to save the new pipeline in database (already exists or wrong name ?).", "", ex)
        log("Pipeline saved in database with id={}".format(pipeline.id))

        # 4- Install lxd container
        image_file_path = os.path.join(root_path, "lxc_image.tar.gz")
        cmd = ["lxc", "image", "import", image_file_path, "--alias", lxd_alias]
        try:
            out_tmp = '/tmp/' + lxd_alias + '-out'
            err_tmp = '/tmp/' + lxd_alias + '-err'
            subprocess.call(cmd, stdout=open(out_tmp, "w"), stderr=open(err_tmp, "w"))
        except Exception as ex:
            raise RegovarException("FAILLED Installation of the lxd image. ($: {})\nPlease, check logs {}".format(" ".join(cmd), err_tmp), "", ex)
        error = open(err_tmp, "r").read()
        if error != "":
            pipeline.delete()
            shutil.rmtree(root_path)
            if "fingerprint" in error:
                raise RegovarException("This pipeline image is already installed on the server. Installation abord.")
            raise RegovarException("FAILLED Lxd image. ($: {}) : \n{}".format(" ".join(cmd), error))
        else:
            log('Installation of the lxd image.')

        # 5- Clean repo (removing image file)
        try:
            os.remove(image_file_path)
        except OSError:
            pass

        log('Pipeline is ready !')

        pipeline.status = "ready"
        pipeline.save()
        return pipeline




    def uninstall_pipeline(self, pipeline, asynch=False):
        """
            Uninstall the pipeline lxd image.
            Database & filesystem clean is done by the core
        """
        if not pipeline or not isinstance(pipeline, Pipeline) :
            raise RegovarException("Pipeline's data error.")
        # Retrieve container settings
        settings = yaml.load(pipeline.manifest)
        lxd_alias = settings["lxd_alias"]
        # Install lxd container
        cmd = ["lxc", "image", "delete", lxd_alias]
        try:
            out_tmp = '/tmp/' + lxd_alias + '-out'
            err_tmp = '/tmp/' + lxd_alias + '-err'
            subprocess.call(cmd, stdout=open(out_tmp, "w"), stderr=open(err_tmp, "w"))
        except Exception as ex:
            raise RegovarException("FAILLED Removing the lxd image {}. ($: {})\nPlease, check logs {}".format(lxd_alias, " ".join(cmd), err_tmp), "", ex)








    def init_job(self, job, asynch=False, auto_notify=True):
        """
            Init a job :
            - check settings (stored in database) 
            - create the lxd container from pipeline image
            - configure container and mount I/O directories to the filesystem

            asynch : execute the start command of the run asynchronously
            auto_notify : tell the container to send 2 notifications :
                          the first one before starting to update status to "running"
                          the last one at the end of the job to update status to "finalizing"
                          if set to false, you will have to monitore yourself the execution of the job
                          to finalize it when its done.
        """
        # Setting up the lxc container for the job
        lxd_container = os.path.basename(job.path)
        manifest = job.pipeline.manifest if isinstance(job.pipeline.manifest, dict) else yaml.load(job.pipeline.manifest)
        lxd_job_cmd = manifest["job"]
        lxd_logs_path = manifest["logs"]
        lxd_inputs_path = manifest["inputs"]
        lxd_outputs_path = manifest["outputs"]
        lxd_db_path = manifest["databases"]
        lxd_image = manifest["lxd_alias"]
        notify_url = NOTIFY_URL.format(job.id)
        inputs_path = os.path.join(job.path, "inputs")
        outputs_path = os.path.join(job.path, "outputs")
        logs_path = os.path.join(job.path, "logs")
        try:
            # create job's start command file
            job_file = os.path.join(job.path, "start_" + lxd_container + ".sh")
            log(job_file)
            with open(job_file, 'w') as f:
                f.write("#!/bin/bash\n")
                if auto_notify:
                    f.write("curl -X POST -d '{{\"status\" : \"running\"}}' {}\n".format(notify_url))
                else:
                    job.status = "running"
                    job.save()

                # TODO : catch if execution return error and notify pirus with error status
                f.write("chmod +x {}\n".format(lxd_job_cmd)) # ensure that we can execute the job's script
                f.write("{} 1> {} 2> {}".format(lxd_job_cmd, os.path.join(lxd_logs_path, 'out.log'), os.path.join(lxd_logs_path, "err.log\n"))) #  || curl -X POST -d '{\"status\" : \"error\"}' " + notify_url + "
                f.write("chown -Rf {}:{} {}\n".format(self.config["pirus_uid"], self.config["pirus_gid"], lxd_outputs_path))
                if auto_notify:
                    f.write("curl -X POST -d '{{\"status\" : \"finalizing\"}}' {}\n".format(notify_url))
                os.chmod(job_file, 0o777)
            # create container
            exec_cmd(["lxc", "init", lxd_image, lxd_container])
            # set up env
            exec_cmd(["lxc", "config", "set", lxd_container, "environment.PIRUS_NOTIFY_URL", notify_url ])
            exec_cmd(["lxc", "config", "set", lxd_container, "environment.PIRUS_CONFIG_FILE", os.path.join(lxd_inputs_path, "config.json") ])
            # Add write access to the container root user to the logsoutputs folders on the host
            exec_cmd(["setfacl", "-Rm", "user:lxd:rwx,default:user:lxd:rwx,user:{0}:rwx,default:user:{0}:rwx".format(self.config["lxd_uid"]), logs_path])
            exec_cmd(["setfacl", "-Rm", "user:lxd:rwx,default:user:lxd:rwx,user:{0}:rwx,default:user:{0}:rwx".format(self.config["lxd_uid"]), outputs_path])
            # set up devices
            exec_cmd(["lxc", "config", "device", "add", lxd_container, "pirus_inputs",  "disk", "source=" + inputs_path,   "path=" + lxd_inputs_path[1:], "readonly=True"])
            exec_cmd(["lxc", "config", "device", "add", lxd_container, "pirus_outputs", "disk", "source=" + outputs_path,  "path=" + lxd_outputs_path[1:]])
            exec_cmd(["lxc", "config", "device", "add", lxd_container, "pirus_logs",    "disk", "source=" + logs_path,     "path=" + lxd_logs_path[1:]])
            exec_cmd(["lxc", "config", "device", "add", lxd_container, "pirus_db",      "disk", "source=" + DATABASES_DIR, "path=" + lxd_db_path[1:], "readonly=True"])
        except Exception as ex:
            raise RegovarException("Unexpected error.", "", ex)

        # Execute the "job" command to start the pipe
        try:
            exec_cmd(["lxc", "start", lxd_container])
            lxd_job_file = os.path.join("/", os.path.basename(job_file))
            exec_cmd(["lxc", "file", "push", job_file, lxd_container + lxd_job_file])

            cmd = ["lxc", "exec", "--mode=non-interactive", lxd_container, "--",  "chmod", "+x", lxd_job_file]
            r, o, e = exec_cmd(cmd)

            cmd = ["lxc", "exec", "--mode=non-interactive", lxd_container, "--", lxd_job_file]
            exec_cmd(cmd, True)
            # TODO : keep future callback and catch error if start command failled

            # if not asynch:
            #     r, o, e = exec_cmd(cmd)
            #     if e.startswith("error: Container is not running."): # catch lxd error
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

        





    def start_job(self, job, asynch=False):
        """
            (Re)Start the job execution. By unfreezing the 
        """
        # Setting up the lxc container for the job
        lxd_container = os.path.basename(job.path)
        r, o, e = exec_cmd(["lxc-start", "-n", lxd_container, "-d"])
        if r != 0:
            err("Error occured when trying to start the job {} (id={})".format(lxd_container, job.id), "$ lxc-start\nstdout ====\n{}\nstderr ====\n{}".format(o, e))
        return r == 0






    def pause_job(self, job, asynch=False):
        """
            Pause the execution of the job.
        """
        lxd_container = os.path.basename(job.path)
        r, o, e = exec_cmd(["lxc-freeze", "-n", lxd_container])
        if r != 0:
            err("Error occured when trying to pause the job {} (id={})".format(lxd_container, job.id), "$ lxc-freeze\nstdout ====\n{}\nstderr ====\n{}".format(o, e))
        return r == 0




    def stop_job(self, job, asynch=False):
        """
            Stop the job. The job is canceled and the container is destroyed.
        """
        lxd_container = os.path.basename(job.path)
        r, o, e = exec_cmd(["lxc-destroy", "-n", lxd_container, "--force"])
        if r != 0:
            err("Error occured when trying to stop the job {} (id={})".format(lxd_container, job.id), "$ lxc-destroy --force\nstdout ====\n{}\nstderr ====\n{}".format(o, e))
        return r == 0



    def monitoring_job(self, job):
        """
            Provide monitoring information about the container (CPU/RAM used, etc)
        """
        lxd_container = os.path.basename(job.path)
        # Result
        result = {}
        # Lxd monitoring data
        try:
            # TODO : to be reimplemented with pylxd api when this feature will be available :)

            r, o, e = exec_cmd(["lxc-info", "-n", lxd_container])
            if r == 0:
                for l in o.split('\n'):
                    data = l.split(': ')
                    if data[0].strip() in ["Name","Created", "Status", "Processes", "Memory (current)", "Memory (peak)"]:
                        result.update({data[0].strip(): data[1]})
        except Exception as ex:
            err("Error occured when retriving monitoring data for job {} (id={})".format(lxd_container, job.id), ex)
        return result



    def finalize_job(self, job, asynch=False):
        """
            IMPLEMENTATION REQUIRED
            Clean temp resources created by the container (log shall be kept), copy outputs file from the container
            to the right place on the server, register them into the database and associates them to the job.
        """
        lxd_container = os.path.basename(job.path)
        # Stop container and clear resource
        try:
            # Clean outputs
            exec_cmd(["lxc-destroy", "-n", lxd_container, "--force"], asynch)
        except Exception as ex:
            err("Error occured when trying to finalize the job {} (id={})".format(lxd_container, job.id), ex)
            return False
        return True 





