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
# FILE MANAGER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class FileManager:
    def __init__(self):
        pass


    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
        """
            Generic method to get files according provided filtering options
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {}
        if order is None:
            order = "name, create_date desc"
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        s = session()
        files = s.query(File).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for f in files: f.init(depth)
        return files




    def upload_init(self, filename, file_size, metadata={}):
        """ 
            Create an entry for the file in the database and return the id of the file in pirus
            This method shall be used to init a resumable upload of a file 
            (the file is not yet available, but we can manipulate its pirus metadata)
        """
        pfile = File.new()
        pfile.name = clean_filename(filename)
        pfile.type = os.path.splitext(filename)[1][1:].strip().lower()
        pfile.path = os.path.join(TEMP_DIR, str(uuid.uuid4()))
        pfile.size = int(file_size)
        pfile.upload_offset = 0
        pfile.status = "uploading"
        pfile.create_date = datetime.datetime.now()
        pfile.save()

        if metadata and len(metadata) > 0:
            pfile.load(metadata)
        log('PirusCore.FileManager.upload_init : New file registered with the id ' + str(pfile.id) + ' (available at ' + pfile.path + ')')
        return pfile



    def upload_chunk(self, file_id, file_offset, chunk_size, chunk):
        """
            Write chunk of data in the file uploading and update model
        """
        # Retrieve file
        pfile = File.from_id(file_id)
        if pfile == None:
            raise RegovarException("Unable to retrieve the pirus file with the provided id : " + file_id)

        # Write file chunk
        try:
            action = "br+" if os.path.lexists(pfile.path) else "bw"
            with open(pfile.path, action) as f:
                f.seek(file_offset)
                f.write(chunk)
        except IOError:
            raise RegovarException("Unable to write file chunk on the the server :(")

        # Update model
        pfile.upload_offset += chunk_size
        pfile.save()

        if pfile.upload_offset == pfile.size:
            self.upload_finish(file_id)

        return pfile



    def upload_finish(self, file_id, checksum=None, checksum_type="md5"):
        """ 
            When upload of a file is finish, we move it from the download temporary folder to the
            files folder. A checksum validation can also be done if provided. 
            Update finaly the status of the file to uploaded or checked -> file ready to be used
        """
        from core.core import core
        # Retrieve file
        pfile = File.from_id(file_id)
        if pfile == None:
            raise RegovarException("Unable to retrieve the pirus file with the provided id : " + file_id)
        # Move file
        old_path = pfile.path
        path = os.path.join(FILES_DIR, str(file_id))
        if not os.path.exists(path): os.makedirs(path)
        pfile.path = os.path.join(path, pfile.name)
        os.rename(old_path, pfile.path)
        # If checksum provided, check that file is correct
        file_status = "uploaded"
        if checksum is not None:
            if checksum_type == "md5" and md5(fullpath) != checksum : 
                raise error
            file_status = "checked"            
        # Update file data in database
        pfile.upload_offset = pfile.size
        pfile.status = file_status
        pfile.save()

        # Check if the file is an image of a Pipeline. if true, automatically start the install
        pipeline = session().query(Pipeline).filter_by(image_file_id=pfile.id).first()
        if pipeline:
            core.pipelines.install(pipeline.id, pipeline.type)
        # Check if the file is an input of a job, try to start the job
        jobs = JobFile.get_jobs_ids(file_id)
        for job in jobs:
            if file_id in job.inputs_ids:
                core.jobs.install(pipeline.id, pipeline.type)



    async def from_url(self, url, metadata={}):
        """ 
            Download a file from url and create a new Pirus file. 
            TODO : implementation have to be fixed
        """
        from core.core import core
        name = clean_filename(os.path.basename(url))
        file = self.upload_init(name, 0)
        # get request and write file
        with open(file.path, "bw+") as f:
            try :
                response = await requests.get(url)
            except Exception as ex:
                raise RegovarException("Error occured when trying to download a file from the provided url : " + str(url), "", ex)
            f.write(response.content)
        pfile.size = os.path.getsize(path)
        pfile.save()
        # save file on the database
        pfile = core.files.upload_finish(file.id)
        return rest_success(pfile)




    def from_local(self, path, move=False, metadata={}):
        """ 
            Copy or move a local file on server and create a new Pirus file. Of course the source file shall have good access rights. 
            TODO : implementation have to be fixed
        """
        if not os.path.isfile(path):
            raise RegovarException("File \"{}\" doesn't exists.".format(path))
        pfile = File.new()
        pfile.load(metadata)
        pfile.name = clean_filename(os.path.basename(path))
        pfile.type = os.path.splitext(pfile.name)[1][1:].strip().lower()
        new_path = os.path.join(FILES_DIR, str(pfile.id))
        if not os.path.exists(new_path): os.makedirs(new_path)
        pfile.path = os.path.join(new_path, pfile.name)
        pfile.size = os.path.getsize(path)
        pfile.upload_offset = 0
        pfile.status = "uploading"
        pfile.create_date = datetime.datetime.now()
        pfile.save()
        try:
            # Move file
            if move:
                os.rename(path, pfile.path)
            else:
                shutil.copyfile(path, pfile.path)
            # Update file data in database
            pfile.upload_offset = pfile.size
            pfile.status = "checked"
            pfile.save()
        except Exception as ex:
            raise RegovarException("Error occured when trying to copy/move the file from the provided path : ".format(path), "", ex)
        return pfile




    def delete(self, file_id):
        pfile = File.from_id(file_id)
        if pfile:
            if os.path.isfile(pfile.path):
                os.remove(pfile.path)
            File.delete(file_id)
        return pfile 
