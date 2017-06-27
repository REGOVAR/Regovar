#!python
# coding: utf-8


import os
import unittest

from config import *
from core.model.file import File
from core.core import core



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TEST PARAMETER / CONSTANTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #




class TestCoreFileManager(unittest.TestCase):
    """ Test case for pirus model File's features. """

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # PREPARATION
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    @classmethod
    def setUpClass(self):
        # Before test we check that we are doing test on a "safe" database
        pass

    @classmethod
    def tearDownClass(self):
        # self.db.drop_database(DATABASE_NAME)
        # shutil.rmtree(TEMP_DIR)
        # shutil.rmtree(FILES_DIR)
        pass



    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # TESTS
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_CRUD_upload(self):
        """ CRUD File with UPLOAD """

        # Upload init
        f = core.files.upload_init("test_upload.tar.gz", 10, {'tags':'Coucou'})
        self.assertEqual(f.name, "test_upload.tar.gz")
        self.assertEqual(f.size, 10)
        self.assertEqual(f.upload_offset, 0)
        self.assertEqual(f.status, "uploading")
        self.assertEqual(f.type, "gz")
        self.assertEqual(f.path.startswith(TEMP_DIR), True)
        old_path = f.path

        # Upload chunk
        f = core.files.upload_chunk(f.id, 0, 5, b'chunk')
        self.assertEqual(f.size, 10)
        self.assertEqual(f.upload_offset, 5)
        self.assertEqual(f.status, "uploading")
        self.assertEqual(os.path.isfile(f.path),True) 
        self.assertEqual(os.path.getsize(f.path), f.upload_offset)

        # Upload finish
        f = core.files.upload_chunk(f.id, 5, 5, b'chunk')
        self.assertEqual(f.size, 10)
        self.assertEqual(f.upload_offset, f.size)
        self.assertEqual(f.status, "uploaded")
        self.assertEqual(f.path.startswith(FILES_DIR), True)
        self.assertEqual(os.path.isfile(old_path), False)
        self.assertEqual(os.path.isfile(f.path), True)
        self.assertEqual(os.path.getsize(f.path), f.size)

        # Check file content
        with open(f.path, "r") as r:
            c = r.readlines()
        self.assertEqual(c, ['chunkchunk'])

        # Delete file
        core.files.delete(f.id)
        f2 = File.from_id(f.id)
        self.assertEqual(f2, None)
        self.assertEqual(os.path.isfile(f.path), False)




    # def test_CRUD_from_url(self):
    #     """ Check that creating file by retrieving it through url is working as expected """

    #     # TODO
    #     pass



    def test_CRUD_local(self):
        """ CRUD File from LOCAL """

        # Create a file into tmp directory
        path = "/tmp/pirus_tu_filemanager_import_from_local.test"
        with open(path, "w") as f:
            f.write("Test it")

        # import it in Pirus
        f = core.files.from_local(path)
        self.assertEqual(os.path.isfile(path),True)
        self.assertEqual(f.name, "pirus_tu_filemanager_import_from_local.test")
        self.assertEqual(f.path.startswith(FILES_DIR), True)
        self.assertEqual(os.path.isfile(f.path),True)
        self.assertEqual(f.status, "checked")
        self.assertEqual(f.size, os.path.getsize(path))

        # Check file content
        with open(f.path, "r") as r:
            c = r.readlines()
        self.assertEqual(c, ['Test it'])

        # Delete file
        core.files.delete(f.id)


