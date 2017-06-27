#!python
# coding: utf-8


import os
import unittest
import asyncio
import time

from config import *
from core.framework.common import run_until_complete
from core.model.file import File
from core.model.pipeline import Pipeline
from core.core import core

from tests.core.fake_container_manager import FakeContainerManager4Test



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TEST PARAMETER / CONSTANTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #








class TestCorePipelineManager(unittest.TestCase):
    """ Test case for pirus model File's features. """

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # PREPARATION
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    @classmethod
    def setUpClass(self):
        CONTAINERS_CONFIG["FakeManager4Test"] = {
            "job_name" : "TU-fake-job-{}",
            "image_name" : "TU-fake-pipe-{}",
        }
        core.container_managers["FakeManager4Test"] = FakeContainerManager4Test()


    @classmethod
    def tearDownClass(self):
        # self.db.drop_database(DATABASE_NAME)
        # shutil.rmtree(TEMP_DIR)
        # shutil.rmtree(FILES_DIR)
        pass



    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # TESTS
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_main_workflow_image_upload(self):
        """ CRUD Pipeline from Image UPLOAD """

        # Upload init
        p, f = core.pipelines.install_init_image_upload("test_image_success.tar.gz", 10, {"type" : "FakeManager4Test"})
        self.assertEqual(f.name, "test_image_success.tar.gz")
        self.assertEqual(f.size, 10)
        self.assertEqual(f.upload_offset, 0)
        self.assertEqual(f.status, "uploading")
        self.assertEqual(f.path.startswith(TEMP_DIR), True)
        self.assertEqual(p.name, f.name)
        self.assertEqual(p.status, "initializing")
        self.assertEqual(p.type, "FakeManager4Test")
        self.assertEqual(p.image_file_id, f.id)

        old_path = f.path

        # Upload chunk
        f = core.files.upload_chunk(f.id, 0, 5, b'chunk')
        self.assertEqual(f.size, 10)
        self.assertEqual(f.upload_offset, 5)
        self.assertEqual(f.status, "uploading")
        self.assertEqual(p.status, "initializing")
        self.assertEqual(core.container_managers["FakeManager4Test"].is_installed, False)

        # Upload finish -> installation shall start automatically as the type have been set
        f = core.files.upload_chunk(f.id, 5, 5, b'chunk')
        self.assertEqual(f.size, 10)
        self.assertEqual(f.upload_offset, f.size)
        self.assertEqual(f.status, "uploaded")
        self.assertEqual(f.path.startswith(FILES_DIR), True)
        self.assertEqual(os.path.isfile(old_path), False)
        self.assertEqual(os.path.isfile(f.path), True)
        self.assertEqual(os.path.getsize(f.path), f.size)

        time.sleep(0.1) # Wait that threads called for the install ends

        # Check that install_pipeline method have been successfully called
        p = Pipeline.from_id(p.id)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_installed, True)
        self.assertEqual(p.status, "ready")

        # Delete pipeline
        pid = p.id
        iid = p.image_file_id
        path = f.path
        r = core.pipelines.delete(pid)
        self.assertEqual(isinstance(r, dict), True)
        self.assertEqual(Pipeline.from_id(pid), None)
        self.assertEqual(File.from_id(iid), None)
        self.assertEqual(os.path.isfile(path), False)




    # def test_workflow_image_url(self):
    #     # TODO
    #     pass



    # def test_workflow_image_local(self):
    #     # TODO
    #     pass


