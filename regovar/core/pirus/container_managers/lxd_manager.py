#!env/python3
# coding: utf-8
import os
import uuid
import json
import yaml
import tarfile
import ipdb
import subprocess

from config import *
from core.framework.common import *

from core.pirus.container_managers.pirus_container_manager import PirusContainerManager
from core.model import *




class LxdManager(PirusContainerManager):
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
        pipeline.load_depth(1)
        if not pipeline.image_file or not pipeline.image_file.path:
            raise RegovarException("Pipeline image file's data error.")

        # 0- retrieve conf related to LXD
        if not CONTAINERS_CONFIG or "lxd" not in CONTAINERS_CONFIG.keys() or not CONTAINERS_CONFIG["lxd"]:
            raise RegovarException("No configuration settings found for lxd")
        conf = CONTAINERS_CONFIG["lxd"]
        lxd_alias = str(uuid.uuid4())
        root_path = os.path.join(PIPELINES_DIR, lxd_alias)
        old_file_path = pipeline.image_file.path
        pipeline.image_file.path = os.path.join(root_path, pipeline.name)
        
        # 1- Copy file into final folder
        log('Installation of the pipeline package : ' + root_path)
        os.makedirs(root_path)
        os.rename(old_file_path, pipeline.image_file.path)
        os.chmod(pipeline.image_file.path, 0o777)

        # 2- Extract pipeline metadata
        try:
            tar = tarfile.open(pipeline.image_file.path)
            tar_data = [info for info in tar.getmembers() if info.name == "metadata.yaml"]
            metadata = tar.extractfile(member=tar_data[0])
            metadata = metadata.read()
            metadata = yaml.load(metadata)  # using yaml as it can also load json
            metadata = metadata["pirus"]
        except:
            # TODO : manage error + remove package file
            err('FAILLED Extraction of ' + pipeline.image_file.path)
            raise RegovarException("XXXX", "Unable to extract package. Corrupted file or wrong format")
        log('Extraction of metadata from ' + pipeline.image_file.path)

        # 2- Check that mandatory fields exists
        missing = ""
        for k in conf["manifest"]["mandatory"].keys():
            if k not in metadata.keys():
                missing += k + ", "                
        if missing != "":
            missing = missing[:-2]
            raise RegovarException("FAILLED Checking validity of metadata (missing : {})".format(missing))
        log('Validity of metadata checked')

        # 3- Default value for optional fields in mandatory file
        for k in conf["manifest"]["default"].keys():
            if k not in metadata.keys():
                metadata[k] = conf["manifest"]["default"][k]

        # 4- Extract pirus technicals files from the tar file
        try:
            if metadata["form"] is not None:
                source = os.path.join("rootfs",metadata['form'][1:] if metadata['form'][0]=="/" else metadata['form'])
                tar_data = [info for info in tar.getmembers() if info.name == source]
                file = tar.extractfile(member=tar_data[0])
                source = os.path.join(root_path, source)
                form_file = os.path.join(root_path, "form.json")
                ui_form = file.read()
                with open(form_file, 'bw+') as f:
                    f.write(ui_form)
            else :
                form_file = os.path.join(root_path, "form.json")
                form_file = b'{}'
                with open(form_file, 'bw+') as f:
                    f.write(form_file)

            source = PIPELINE_DEFAULT_ICON_PATH
            icon_file = os.path.join(root_path, "icon.png")
            if metadata["icon"] is not None:
                source = os.path.join("rootfs", metadata['icon'][1:] if metadata['icon'][0]=="/" else metadata['icon'])
                try:
                    tar_data = [info for info in tar.getmembers() if info.name == source]
                    file = tar.extractfile(member=tar_data[0])
                    source = os.path.join(root_path, source)
                    icon_file = os.path.join(root_path, os.path.basename(metadata['icon']))
                    with open(icon_file, 'bw+') as f:
                        f.write(file.read())
                except:
                    war("Icon file not found in the image archive : {}. Using default icon.".format(source))
                    shutil.copyfile(PIPELINE_DEFAULT_ICON_PATH, icon_file)
            else:
                shutil.copyfile(source, icon_file)
        except Exception as ex:
            raise RegovarException("Error occure during extraction of pipeline technical files (form.json / icon) from image file : {}".format(pipeline.image_file.path), "", ex)
        log('Extraction of pipeline technical files (form.json / icon)')

        # 5- Save pipeline into database
        lxd_alias = conf["image_name"].format(lxd_alias)
        metadata["lxd_alias"] = lxd_alias
        pipeline.load(metadata)
        pipeline.vm_settings = yaml.dump(metadata)
        pipeline.status = "installing"
        pipeline.ui_form = ui_form.decode()
        pipeline.ui_icon = icon_file
        pipeline.root_path = root_path
        try:
            pipeline.save()
        except Exception as ex:
            raise RegovarException("FAILLED to save the new pipeline in database (already exists or wrong name ?).", "", ex)

        log("Pipeline saved in database with id={}".format(pipeline.id))

        # 6- Install lxd container
        cmd = ["lxc", "image", "import", pipeline.image_file.path, "--alias", lxd_alias]
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
            raise RegovarException("FAILLED Lxd image. ($: {}) : \n{}".format(" ".join(cmd), error))
        else:
            log('Installation of the lxd image.')

        # 7- Clean directory
        try:
            keep = [pipeline.image_file.path, form_file, icon_file]
            for f in os.listdir(root_path):
                fullpath = os.path.join(root_path, f)
                if fullpath not in keep:
                    if os.path.isfile(fullpath):
                        os.remove(fullpath)
                    else:
                        shutil.rmtree(fullpath)
        except Exception as ex:
            # Notify only admins
            err('FAILLED to clean repository : {}'.format(ex))
        log('Cleaning repository.')
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
        settings = yaml.load(pipeline.vm_settings)
        lxd_alias = settings["lxd_alias"]
        # Install lxd container
        cmd = ["lxc", "image", "delete", lxd_alias]
        try:
            out_tmp = '/tmp/' + lxd_alias + '-out'
            err_tmp = '/tmp/' + lxd_alias + '-err'
            subprocess.call(cmd, stdout=open(out_tmp, "w"), stderr=open(err_tmp, "w"))
        except Exception as ex:
            raise RegovarException("FAILLED Removing the lxd image {}. ($: {})\nPlease, check logs {}".format(lxd_alias, " ".join(cmd), err_tmp), "", ex)








    def init_job(self, job, asynch=False):
        """
            Init a job :
            - check settings (stored in database) 
            - create the lxd container from pipeline image
            - configure container and mount I/O directories to the filesystem
        """
        # Setting up the lxc container for the job
        lxd_container = os.path.basename(job.root_path)
        vm_settings = yaml.load(job.pipeline.vm_settings)
        lxd_job_cmd = vm_settings["job"]
        lxd_logs_path = vm_settings["logs"]
        lxd_inputs_path = vm_settings["inputs"]
        lxd_outputs_path = vm_settings["outputs"]
        lxd_db_path = vm_settings["databases"]
        lxd_image = vm_settings["lxd_alias"]
        notify_url = NOTIFY_URL.format(job.id)
        inputs_path = os.path.join(job.root_path, "inputs")
        outputs_path = os.path.join(job.root_path, "outputs")
        logs_path = os.path.join(job.root_path, "logs")
        try:
            # create job's start command file
            job_file = os.path.join(job.root_path, "start_" + lxd_container + ".sh")
            log(job_file)
            with open(job_file, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("curl -X POST -d '{{\"status\" : \"running\"}}' {}\n".format(notify_url))
                # TODO : catch if execution return error and notify pirus with error status
                f.write("chmod +x {}\n".format(lxd_job_cmd)) # ensure that we can execute the job's script
                f.write("{} 1> {} 2> {}".format(lxd_job_cmd, os.path.join(lxd_logs_path, 'out.log'), os.path.join(lxd_logs_path, "err.log\n"))) #  || curl -X POST -d '{\"status\" : \"error\"}' " + notify_url + "
                f.write("chown -Rf {}:{} {}\n".format(self.config["pirus_uid"], self.config["pirus_gid"], lxd_outputs_path))
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
            exec_cmd(["lxc", "exec", lxd_container, "--",  "chmod", "+x", lxd_job_file])

            cmd = ["lxc", "exec", lxd_container, lxd_job_file]
            if not asynch:
                r, o, e = exec_cmd(cmd)
                if e.startswith("error: Container is not running."): # catch lxd error
                    job.status = "error"
                    job.save()
                    err('Error occured when starting the job {} (id={}).\n{}'.format(job.name, job.id, e))
                else:
                    log('New job {} (id={}) start with success.'.format(job.name, job.id))
            else:
                subprocess.Popen(cmd)
                return True
        except Exception as ex:
            raise RegovarException("Unexpected error.", "", ex)

        return True

        





    def start_job(self, job, asynch=False):
        """
            (Re)Start the job execution. By unfreezing the 
        """
        # Setting up the lxc container for the job
        lxd_container = os.path.basename(job.root_path)
        r, o, e = exec_cmd(["lxc", "start", lxd_container])
        if r != 0:
            err("Error occured when trying to start the job {} (id={})".format(lxd_container, job.id), "$ lxc start\nstdout ====\n{}\nstderr ====\n{}".format(o, e))
        return r == 0






    def pause_job(self, job, asynch=False):
        """
            Pause the execution of the job.
        """
        lxd_container = os.path.basename(job.root_path)
        r, o, e = exec_cmd(["lxc", "pause", lxd_container])
        if r != 0:
            err("Error occured when trying to pause the job {} (id={})".format(lxd_container, job.id), "$ lxc pause\nstdout ====\n{}\nstderr ====\n{}".format(o, e))
        return r == 0




    def stop_job(self, job, asynch=False):
        """
            Stop the job. The job is canceled and the container is destroyed.
        """
        lxd_container = os.path.basename(job.root_path)
        r, o, e = exec_cmd(["lxc", "delete", lxd_container, "--force"])
        if r != 0:
            err("Error occured when trying to stop the job {} (id={})".format(lxd_container, job.id), "$ lxc delete --force\nstdout ====\n{}\nstderr ====\n{}".format(o, e))
        return r == 0



    def monitoring_job(self, job, asynch=False):
        """
            Provide monitoring information about the container (CPU/RAM used, etc)
        """
        lxd_container = os.path.basename(job.root_path)
        # Result
        result = {}
        # Lxd monitoring data
        try:
            # TODO : to be reimplemented with pylxd api when this feature will be available :)
            out = subprocess.check_output(["lxc", "info", lxd_container])
            for l in out.decode().split('\n'):
                data = l.split(': ')
                if data[0].strip() in ["Name","Created", "Status", "Processes", "Memory (current)", "Memory (peak)"]:
                    result.update({data[0].strip(): data[1]})
        except Exception as ex:
            err("Error occured when trying to finalize the job {} (id={})".format(lxd_container, job.id), ex)
        return result



    def finalize_job(self, job, asynch=False):
        """
            IMPLEMENTATION REQUIRED
            Clean temp resources created by the container (log shall be kept), copy outputs file from the container
            to the right place on the server, register them into the database and associates them to the job.
        """
        lxd_container = os.path.basename(job.root_path)
        # Stop container and clear resource
        try:
            # Clean outputs
            exec_cmd(["lxc", "delete", lxd_container, "--force"], asynch)
        except Exception as ex:
            err("Error occured when trying to finalize the job {} (id={})".format(lxd_container, job.id), ex)
            return False
        return True 





