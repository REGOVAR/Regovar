#!python
# coding: utf-8


import os
import sys
import shutil
import unittest
import json
import time

from config import *
from core.framework.common import *
from core.model.file import File
from core.core import core

from tests.core.fake_container_manager import FakeContainerManager4Test

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TEST PARAMETER / CONSTANTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #




class TestCoreJobManager(unittest.TestCase):
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
        core.container_managers["FakeManager4Test"].need_image_file = False

    @classmethod
    def tearDownClass(self):
        # self.db.drop_database(DATABASE_NAME)
        # shutil.rmtree(TEMP_DIR)
        # shutil.rmtree(FILES_DIR)
        pass



    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # TESTS
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_main_workflow(self):
        """ Check that job core's workflow, for job, is working as expected. """

        # install the fake pipeline
        p = core.pipelines.install_init("test_image_success", {"type" : "FakeManager4Test"})
        core.pipelines.install(p.id, asynch=False)

        self.assertEqual(core.container_managers["FakeManager4Test"].is_init, False)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_running, False)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_monitoring, False)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_paused, False)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_stoped, False)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_monitoring, False)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_finalized, False)


        # init job 
        job = core.jobs.new(p.id, "Test job success", {}, asynch=False)
        job_id = job.id
        self.assertEqual(core.container_managers["FakeManager4Test"].is_init, True)
        self.assertEqual(job.name, "Test job success")
        self.assertEqual(os.path.exists(job.path), True)
        self.assertEqual(os.path.exists(os.path.join(job.path, "inputs")), True)
        self.assertEqual(os.path.exists(os.path.join(job.path, "outputs")), True)
        self.assertEqual(os.path.exists(os.path.join(job.path, "logs")), True)
        self.assertEqual(os.path.isfile(os.path.join(job.path, "inputs/config.json")), True)

        # call all delayed action 
        # FIXME : why assertRaise crash the test :/
        # self.assertRaises(RegovarException, core.jobs.start(job_id, asynch=False))
        # self.assertEqual(core.container_managers["FakeManager4Test"].is_running, True)

        job = core.jobs.monitoring(job_id)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_monitoring, True)

        core.jobs.pause(job_id, asynch=False)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_paused, True)

        core.jobs.start(job_id, asynch=False)
        core.jobs.stop(job_id, asynch=False)
        self.assertEqual(core.container_managers["FakeManager4Test"].is_stoped, True)

        with self.assertRaises(RegovarException):
            core.jobs.finalize(job_id, asynch=False)
        job = core.jobs.monitoring(job_id)
        self.assertEqual(job.status, "canceled")
        self.assertEqual(core.container_managers["FakeManager4Test"].is_finalized, False)

        core.jobs.delete(job_id, asynch=False)
        self.assertEqual(os.path.isfile(os.path.join(job.path, "inputs/config.json")), False)
        self.assertEqual(os.path.exists(os.path.join(job.path, "inputs")), False)
        self.assertEqual(os.path.exists(os.path.join(job.path, "outputs")), False)
        self.assertEqual(os.path.exists(os.path.join(job.path, "logs")), False)
        self.assertEqual(os.path.exists(job.path), False)





