#!env/python3
# coding: utf-8
import ipdb

import os
import shutil
import json
import zipfile
import datetime
import time
import uuid
import subprocess
import requests



from config import *
from core.framework.common import *
from core.framework.postgresql import execute
from core.model import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# PIPELINE MANAGER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class PipelineManager:
    def __init__(self):
        pass


    def list(self):
        """
            List all pipelines with minimum of data
        """
        sql = "SELECT id, name, type, status, description, version, image_file_id, starred, installation_date, manifest, documents FROM pipeline ORDER BY id"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "name": res.name,
                "description": res.description,
                "type": res.type,
                "status": res.status,
                "version": res.version,
                "image_file_id": res.image_file_id,
                "starred": res.starred,
                "installation_date": res.installation_date.isoformat(),
                "manifest": res.manifest,
                "documents": res.documents
            })
        return result

    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
        """
            Generic method to get pipelines according provided filtering options
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {}
        if order is None:
            order = "name, installation_date desc"
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        pipes = Session().query(Pipeline).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for p in pipes: p.init(depth)
        return pipes



    def install_init (self, name, metadata={}):
        pipe = Pipeline.new()
        pipe.name = name
        pipe.status = "initializing"
        pipe.save()

        if metadata and len(metadata) > 0:
            pipe.load(metadata)
        log('core.PipeManager.register : New pipe registered with the id {}'.format(pipe.id))
        return pipe



    def install_init_image_upload(self, filepath, file_size, pipe_metadata={}):
        """ 
            Initialise a pipeline installation. 
            To use if the image have to be uploaded on the server.
            Create an entry for the pipeline and the file (image that will be uploaded) in the database.
            Return the Pipeline and the File objects created

            This method shall be used to init a resumable upload of a pipeline 
            (the pipeline/image are not yet installed and available, but we need to manipulate them)
        """
        from core.core import core

        pfile = core.files.upload_init(filepath, file_size)
        pipe = self.install_init(filepath, pipe_metadata)
        pipe.image_file_id = pfile.id
        pipe.save()
        return pipe, pfile



    async def install_init_image_url(self, url, pipe_metadata={}):
        """ 
            Initialise a pipeline installation. 
            To use if the image have to be retrieved via an url.
            Create an entry for the pipeline and the file (image) in the database.
            Async method as the download start immediatly, followed by the installation when it's done

            Return the Pipeline object ready to be used
        """
        raise NotImplementedError("TODO")



    def install_init_image_local(self, filepath, move=False, pipe_metadata={}):
        """ 
            Initialise a pipeline installation. 
            To use if the image have to be retrieved on the local server.
            Create an entry for the pipeline and the file (image) in the database.
            Copy the local file into dedicated Pirus directory and start the installation of the Pipeline

            Return the Pipeline object ready to be used
        """
        from core.core import core

        pfile = core.files.from_local(filepath, move)
        pipe = self.install_init(os.path.basename(filepath), pipe_metadata)

        # FIXME: Sometime getting sqlalchemy error 'is not bound to a Session' 
        # why it occure here ... why sometime :/ 
        check_session(pfile)
        check_session(pipe)

        pipe.image_file_id = pfile.id
        pipe.save()
        return pipe




    def install(self, pipeline_id, asynch=True):
        """
            Start the installation of the pipeline. (done in another thread)
            The initialization shall be done (image ready to be used)
        """
        from core.core import core

        pipeline = Pipeline.from_id(pipeline_id, 1)
        if not pipeline : 
            raise RegovarException("Pipeline not found (id={}).".format(pipeline_id))
        if pipeline.status != "initializing":
            raise RegovarException("Pipeline status ({}) is not \"initializing\". Cannot perform another installation.".format(pipeline.status))
        if pipeline.image_file and pipeline.image_file.status not in ["uploading", "uploaded", "checked"]:
            raise RegovarException("Wrong pipeline image (status={}).".format(pipeline.image_file.status))

        if not pipeline.image_file or pipeline.image_file.status in ["uploaded", "checked"]:
            if asynch:
                run_async(self.__install, pipeline)
            else:
                pipeline = self.__install(pipeline)

        return pipeline



    def check_manifest(self, manifest):
        """
            Check that manifest (json) is valid and return the full version completed 
            with default values if needed
        """
        missing = ""
        for k in ["name", "version"]:
            if k not in manifest.keys():
                missing += k + ", "                
        if missing != "":
            missing = missing[:-2]
            raise RegovarException("FAILLED Checking validity of manifest (missing : {})".format(missing))

        # 2- Default value for optional fields in mandatory file
        default = {
            "description": "",
            "type": "job",
            "contacts": [],
            "regovar_db_access": False,
            "inputs": "/pipeline/inputs",
            "outputs": "/pipeline/outputs",
            "databases": "/pipeline/databases",
            "logs": "/pipeline/logs"
        }
        for k in default.keys():
            if k not in manifest.keys():
                manifest[k] = default[k]

        # 3- check type
        if manifest["type"] not in ["job", "importer", "exporter", "reporter"]:
            raise RegovarException("FAILLED Checking validity of manifest (type '{}' not supported)".format(manifest["type"]))


        log('Validity of manifest checked')
        return manifest



    def __install(self, pipeline):
        from core.core import core
        # Dezip pirus package in the pirus pipeline directory
        root_path = os.path.join(PIPELINES_DIR, str(pipeline.id))
        log('Installation of the pipeline package : ' + root_path)
        os.makedirs(root_path)
        os.chmod(pipeline.image_file.path, 0o777)

        # TODO: Check zip integrity and security before extracting it
        #       see python zipfile official doc
        with zipfile.ZipFile(pipeline.image_file.path,"r") as zip_ref:
            zip_ref.extractall(root_path)

            # check package tree
            # find root folder
            files = [i.filename for i in zip_ref.infolist()]
            for f in files:
                if f.endswith("manifest.json"): break
            zip_root = os.path.dirname(f)
            # remove intermediate folder
            if zip_root != "":
                zip_root = os.path.join(root_path, zip_root)
                for filename in os.listdir(zip_root):
                    shutil.move(os.path.join(zip_root, filename), os.path.join(root_path, filename))
                os.rmdir(zip_root)

        # Load manifest

        try:
            log(os.path.join(root_path, "manifest.json"))
            with open(os.path.join(root_path, "manifest.json"), "r") as f:
                data = f.read()
                log(data)
                manifest = json.loads(data)
                manifest = self.check_manifest(manifest)
                pipeline.developpers = manifest.pop("contacts")
                pipeline.manifest = manifest 

                # list documents available
                pipeline.documents = {
                    "about": os.path.join(root_path, "doc/about.html"),
                    "help": os.path.join(root_path, "doc/help.html"),
                    "icon": os.path.join(root_path, "doc/icon.png"),
                    "icon2": os.path.join(root_path, "doc/icon.jpg"),
                    "license":os.path.join(root_path, "LICENSE"),
                    "readme": os.path.join(root_path, "README")
                }
                for k in pipeline.documents.keys():
                    if not os.path.exists(pipeline.documents[k]):
                        pipeline.documents[k] = None
                p = pipeline.documents.pop("icon2")
                if not pipeline.documents["icon"]:
                    pipeline.documents["icon"] = p

                pipeline.save()
        except Exception as ex:
            pipeline.status = "error"
            pipeline.save()
            raise RegovarException("Unable to open and read manifest.json. The pipeline package is wrong or corrupt.", exception=ex)
        
        # Update and save pipeline status
        pipeline.type = manifest["type"]
        pipeline.installation_date = datetime.datetime.now()
        pipeline.status = "installing"
        pipeline.save()
        
        # Install pipeline
        result = core.container_manager.install_pipeline(pipeline)
        return result







    def delete(self, pipeline_id, asynch=True):
        """
            Start the uninstallation of the pipeline. (done in another thread)
            Remove image file if exists.
        """
        from core.core import core

        result = None
        pipeline = Pipeline.from_id(pipeline_id, 1)
        if pipeline:
            result = pipeline.to_json()
            # Clean container
            try:
                if asynch: 
                    run_async(self.__delete, pipeline) 
                else: 
                    self.__delete(pipeline)
            except Exception as ex:
                war("core.PipelineManager.delete : Container manager failed to delete the container with id {}.".format(pipeline.id))
            try:
                # Clean filesystem
                shutil.rmtree(pipeline.path, True)
                # Clean DB
                core.files.delete(pipeline.image_file_id)
                Pipeline.delete(pipeline.id)
            except Exception as ex:
                raise RegovarException("core.PipelineManager.delete : Unable to delete the pipeline's pirus data for the pipeline {}.".format(pipeline.id), ex)
        return result


    def __delete(self, pipeline):
        from core.core import core
        
        try:
            core.container_manager.uninstall_pipeline(pipeline)
        except Exception as ex:
            raise RegovarException("Error occured during uninstallation of the pipeline. Uninstallation aborded.", ex)
 
