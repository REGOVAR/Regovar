#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp

import aiohttp_jinja2
import tarfile
import datetime
import time
import uuid


from aiohttp import web
from urllib.parse import parse_qsl


from config import *
from core.framework.common import *
from core.framework.tus import *
from core.model import *
from core.core import core
from api_rest.rest import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Customization of the TUS protocol for the download of pirus files
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# File TUS wrapper
class FileWrapper (TusFileWrapper):
    def __init__(self, id):
        self.file = File.from_id(id)
        if self.file is not None:
            self.id = id
            self.name = self.file.name
            self.upload_offset = self.file.upload_offset
            self.path = self.file.path
            self.size = self.file.size
            self.upload_url = "file/upload/" + str(id)
        else:
            raise RegovarException("TUS File wrapper init error : Unknow id: {}".format(id))


    def save(self):
        from core.core import core
        try:
            f = File.from_id(self.id)
            f.upload_offset=self.upload_offset
            f.save()
            core.notify_all(self=None, data={"action": "file_upload", "data" : f.to_json()})
        except Exception as ex:
            return TusManager.build_response(code=500, body="Unexpected error occured: {}".format(ex))


    def complete(self, checksum=None, checksum_type="md5"):
        try:
            log ('Upload of the file (id={0}) is complete.'.format(self.id))
            core.files.upload_finish(self.id, checksum, checksum_type)
            f = File.from_id(self.id)
            core.notify_all(self=None, data={"action": "file_upload", "data" : f.to_json()})
        except Exception as ex:
            return TusManager.build_response(code=500, body="Unexpected error occured: {}".format(ex))


    @staticmethod
    def new_upload(request, filename, file_size):
        """ 
            Create and return the wrapper to manipulate the uploading file
        """
        pfile = core.files.upload_init(filename, file_size)
        return FileWrapper(pfile.id)



# set mapping
tus_manager.route_maping["/file/upload"] = FileWrapper












# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# REST FILE API HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 




class FileHandler:

    def list(self, request):
        # Generic processing of the get query
        fields, query, order, offset, limit = process_generic_get(request.query_string, File.public_fields)
        depth = request.query["depth"] if "depth" in request.query else 0
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : File.count(),
            "range_max"    : RANGE_MAX,
        }
        # Return result of the query for PirusFile 
        files = core.files.get(fields, query, order, offset, limit, depth)
        return rest_success([f.to_json() for f in files], range_data)




    async def edit(self, request):
        # TODO : implement PUT to edit file metadata (and remove the obsolete  "simple post" replaced by TUS upload )
        file_id = request.match_info.get('file_id', "")
        params = await request.json()
        return rest_error("Not yet implemented")
        


    def delete(self, request):
        file_id = request.match_info.get('file_id', "")
        try:
            return rest_success(core.files.delete(file_id).to_json())
        except Exception as ex:
            return rest_error("Error occured : " + str(ex))



    def get(self, request):
        file_id = request.match_info.get('file_id', -1)
        file = File.from_id(file_id, 2)
        if not file:
            return rest_error("Unable to find the file (id={})".format(file_id))
        return rest_success(file.to_json(File.public_fields))



    # Resumable download implement the TUS.IO protocol.
    def tus_config(self, request):
        return tus_manager.options(request)

    def tus_upload_init(self, request):
        return tus_manager.creation(request)

    def tus_upload_resume(self, request):
        return tus_manager.resume(request)

    async def tus_upload_chunk(self, request):
        result = await tus_manager.patch(request)
        return result

    def tus_upload_delete(self, request):
        return tus_manager.delete_file(request)






