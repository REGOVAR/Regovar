#!env/python3
# coding: utf-8
import ipdb




import base64
import os
import uuid


from aiohttp import web
# from core import *



TUS_API_VERSION = "1.0.0"
TUS_API_VERSION_SUPPORTED = "1.0.0"
TUS_MAX_SIZE = 6250000000 # 50 Go
TUS_EXTENSION = ['creation', 'termination', 'file-check']





# TUS wrapper interface
class TusFileWrapper:
    id = "<unique id of the file>"
    name = "<filename>"
    size = "<total size of the file in bytes>"
    upload_offset = "<upload offset position>"
    path = "<path where the file is saved on the server>"
    upload_url = "<url that the client shall used to upload the file>"
    
    def start(self):
        # Do something to start an upload (creating index in db by example)
        pass

    def save(self):
        # Do something when the upload of a chunk of the file is done. Basicaly : save new offset position in a database
        pass

    def complete(self, checksum=None, checksum_type="md5"):
        # Do something when the upload of the file is finished
        pass

    @staticmethod
    def from_request(request):
        """ Return the wrapper to manipulate the uploading file """
        if request == None:
            return TusManager.build_response(code=404)
        id = request.match_info.get('file_id', -1)
        if id == -1:
            return TusManager.build_response(code=404)

        # We can upload file or custom annotation db, we check model according to url
        for k in TusManager.route_maping.keys():
            if k in request.raw_path:
                return TusManager.route_maping[k](id)
        return TusManager.build_response(code=404)

    @staticmethod
    def new_upload(request, filename, file_size):
        # Create and return the wrapper to manipulate the uploading file
        if request == None:
            return TusManager.build_response(code=404)

        for k in TusManager.route_maping.keys():
            if k in request.raw_path:
                return TusManager.route_maping[k].new_upload(request, filename, file_size)










# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# TUS.IO Protocal manager - GENERIC IMPLEMENTATION 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
class TusManager:

    route_maping = {}


    @staticmethod
    def build_response(code, headers={}, body=""):
        h = {'Tus-Resumable' : TUS_API_VERSION,  'Tus-Version' : TUS_API_VERSION_SUPPORTED}
        h.update(headers)
        return web.Response(body=body.encode(), status=code, headers=h)



    # HEAD request done by client to retrieve the offset where the upload of the file shall be resume
    def resume(self, request):
        fw = TusFileWrapper.from_request(request)
        return TusManager.build_response(code=200, headers={ 'Upload-Offset' : str(fw.upload_offset), 'Cache-Control' : 'no-store' })



    # PATCH request done by client to upload a chunk a of file.
    async def patch(self, request):
        fw = TusFileWrapper.from_request(request)
        data = await request.content.read()
        if fw.name is None or os.path.lexists( fw.path ) is False:
            # logger.info( "PATCH sent for resource_id that does not exist. {}".format( fw.id))
            return TusManager.build_response(code=410)
        file_offset = int(request.headers.get("Upload-Offset", 0))
        chunk_size = int(request.headers.get("Content-Length", 0))
        if file_offset != fw.upload_offset: # check to make sure we're in sync
            return TusManager.build_response(code=409) # HTTP 409 Conflict
        try:
            with open(fw.path, "br+") as f:
                f.seek( file_offset )
                f.write(data)
        except IOError:
            return TusManager.build_response(code=500, body="Unable to write file chunk on the the server :(")

        fw.upload_offset += chunk_size
        fw.save()
        # file transfer complete
        if fw.size == fw.upload_offset: 
            fw.complete()
        headers = { 'Upload-Offset' : str(fw.upload_offset), 'Tus-Temp-Filename' : str(fw.id) }
        return TusManager.build_response(code=200, headers=headers)



    # OPTIONS request done by client to know how the server is convigured
    def options(self, request):
        return TusManager.build_response(code=204, headers={ 'Tus-Extension' : ",".join(TUS_EXTENSION), 'Tus-Max-Size' : str(TUS_MAX_SIZE) })



    # POST request done by client to start a new resumable upload
    def creation(self, request):
        if request.headers.get("Tus-Resumable", None) is None:
            return TusManager.build_response(code=500, body="Received File upload for unsupported file transfer protocol")

        # process upload metadata
        metadata = {}
        for kv in request.headers.get("Upload-Metadata", None).split(","):
            key, value = kv.split(" ")
            metadata[key] = base64.b64decode(value)

        # Retrieve data about the file
        filename  = metadata.get("filename").decode()
        file_size = int(request.headers.get("Upload-Length", "0"))

        # Create file entry in database
        fw = TusFileWrapper.new_upload(request, filename, file_size)

        # create empty file at the provided location
        try:
            os.mknod(fw.path)
        except IOError as e:
            return TusManager.build_response(code=500, body="Unable to create file: {}".format(e))

        return TusManager.build_response(code=201, headers={'Location' : fw.upload_url, 'Tus-Temp-Filename' : str(fw.id)})



    # DELETE request done by client to delete a file
    def delete_file(self, request):
        fw = TusFileWrapper.from_request(request)
        os.unlink(fw.path)
        annso.sample.delete_files(fw.id)
        return TusManager.build_response(code=204)



    # GET request !!! Not implemented - Trash code !!!
    # def exists(self, request):
    #     metadata = {}
    #     for kv in request.headers.get("Upload-Metadata", None).split(","):
    #         key, value = kv.split(" ")
    #         metadata[key] = base64.b64decode(value)

    #     if metadata.get("filename", None) is None:
    #         return TusManager.build_response(code=404, body="metadata filename is not set")

    #     filename_name, extension = os.path.splitext( metadata.get("filename").decode())
    #     h={}
    #     if filename_name.upper() in [os.path.splitext(f)[0].upper() for f in os.listdir( os.path.dirname( self.upload_folder ))]:
    #         h.update({'Tus-File-Name' : metadata.get("filename").decode(), 'Tus-File-Exists' : True})
    #     else:
    #         h.update({'Tus-File-Exists' : False})
    #     return TusManager.build_response(code=200, headers=h)



        









# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Instanciate manager 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
tus_manager = TusManager()