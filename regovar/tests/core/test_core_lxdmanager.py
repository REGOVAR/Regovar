#!python
# coding: utf-8

import ipdb

import os
import sys
import shutil
import unittest
import subprocess
import yaml
import time

from config import *
from core.framework.common import *
from core.model import *
from core.core import core


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TEST PARAMETER / CONSTANTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #





class TestCoreLxdManager(unittest.TestCase):
    """ Test case for lxd container management. """

    IMAGE_FILE_PATH = "/var/regovar/_pipes/PirusTest.tar.gz"
    MAX_WAITING_4_INSTALL = 60 # 60s (actually, installing PirusSimple need ~45s)



    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # PREPARATION
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    @classmethod
    def setUpClass(self):
        pass
        

    @classmethod
    def tearDownClass(self):
        pass



    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # TESTS
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_000_pipeline_image_installation(self):
        """ Check that installation of the PirusSimpleContainer from local image file is working. """

        # install the fake pipeline
        p = core.pipelines.install_init_image_local(self.IMAGE_FILE_PATH, move=False, pipe_metadata={"type" : "lxd"})
        core.pipelines.install(p.id, asynch=False)  # install it synchronously to be able to test correctly
        TestCoreLxdManager.pid = p.id

        # waiting = self.MAX_WAITING_4_INSTALL
        # success = False
        # while waiting > 0:
        #     time.sleep(1)
        #     waiting -= 1
        #     if Pipeline.from_id(TestCoreLxdManager.pid).status == "ready":
        #         break;

        p = Pipeline.from_id(TestCoreLxdManager.pid, 1)
        self.assertEqual(p.status, "ready")
        self.assertEqual(os.path.isfile(self.IMAGE_FILE_PATH), True)
        self.assertNotEqual(self.IMAGE_FILE_PATH, p.image_file.path)

        # test that documents key is no more present in the manifest
        self.assertEqual("documents" not in p.manifest, True)



    def test_100_job_CRUD_normal_workflow(self):
        """ Check lxd job's normal worklow. """

        fake_config = {
            "file1" : "",
            "duration" : 20,
            "crash" : False,
            "outfilename" : "result.txt",
            "notification_enable" : False # as by running in TU we didn't have server to answer
        }



        # Create a new job
        job = core.jobs.new(TestCoreLxdManager.pid, "job4test", fake_config, asynch=False, auto_notify=False)
        lxd_name = os.path.basename(job.path)
        self.assertEqual(job.status, "running")
        self.assertEqual(os.path.exists(job.path), True)
        self.assertEqual(os.path.exists(os.path.join(job.path, "inputs", "config.json")), True)
        self.assertEqual(lxd_name in exec_cmd(["lxc", "list"])[1], True)
        self.assertEqual("Status: Running" in exec_cmd(["lxc", "info", lxd_name])[1], True)
        # TODO check config.json : retrieve fake_config with the "job" key and a notification url in "pirus" key
        

        # monotoring when job is running
        job = core.jobs.monitoring(job.id)
        self.assertEqual(job.status, "running")
        self.assertEqual(isinstance(job.logs_moninitoring, dict), True)
        self.assertEqual('Memory (current)' in job.logs_moninitoring.keys(), True)
        self.assertEqual(job.logs_moninitoring['Status'], 'Running')
        self.assertEqual(job.logs_moninitoring['Name'], lxd_name)
        self.assertEqual(os.path.exists(os.path.join(job.path, "logs", "out.log")), True)
        self.assertEqual(len(job.logs), 2)
        olog = job.logs[0]
        self.assertEqual(olog.name, "out.log")
        self.assertEqual(olog.head(1), "START Plugin de test\n")

        # pause the job
        core.jobs.pause(job.id, asynch=False)
        self.assertEqual(job.status, "pause")


        # monotoring when the job is paused
        job = core.jobs.monitoring(job.id)
        self.assertEqual(job.status, "pause")
        self.assertEqual(job.logs_moninitoring['Status'], 'Frozen')


        # restart the job
        core.jobs.start(job.id, asynch=False)
        job = core.jobs.monitoring(job.id)
        self.assertEqual(job.status, "running")
        self.assertEqual(job.logs_moninitoring['Status'], 'Running')


        # finalize the job
        core.jobs.finalize(job.id, asynch=False)
        job = Job.from_id(job.id)
        self.assertEqual(job.status, "done")
        # Todo check path for inputs, outputs, logs
        # Todo check output stored in database and file no more in outputs (just slinks)
        # Todo check log out/err
        job = core.jobs.monitoring(job.id)
        self.assertEqual(job.logs_moninitoring, {})




    def test_900_pipeline_image_deletion(self):
        # uninstall the pipeline
        p0 = Pipeline.from_id(TestCoreLxdManager.pid, 1)
        pid = p0.id
        ppath = p0.image_file.path
        iid = p0.image_file_id
        rpath = p0.path
        manifest = p0.manifest
        core.pipelines.delete(p0.id, False)  # delete it synchronously to be able to test correctly

        # check that image file no more exists
        self.assertEqual(os.path.isfile(ppath), False)
        f = File.from_id(iid)
        self.assertEqual(f, None)

        # check that pipeline no more exists
        self.assertEqual(os.path.exists(rpath), False)
        p1 = Pipeline.from_id(pid)
        self.assertEqual(p1, None)

        # check that lxd image no more exists
        lxd_alias = yaml.load(manifest)["lxd_alias"]
        r, o, e = exec_cmd(["lxc", "image", "list"])
        self.assertEqual(r, 0)
        self.assertEqual(lxd_alias in o, False)



