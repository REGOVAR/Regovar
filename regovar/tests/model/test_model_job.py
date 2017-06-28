#!python
# coding: utf-8


import os
import sys
import shutil
import unittest
import json
import time

from config import DATABASE_NAME
from core.model import *



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TEST PARAMETER / CONSTANTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
TU_PUBLIC_FIELDS = ["id", "pipeline_id", "pipeline", "config", "create_date", "update_date", "status", "progress_value", "progress_label", "inputs_ids", "outputs_ids", "inputs", "outputs", "path", "logs", "name"]





class TestModelJob(unittest.TestCase):
    """ MODEL Unit Tests : Job """

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # PREPARATION
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    @classmethod
    def setUpClass(self):
        # Before test we check that we are doing test on a "safe" database
        if DATABASE_NAME[-5:] != "_test": raise Exception("Wrong config database used")

    @classmethod
    def tearDownClass(self):
        # self.db.drop_database(DATABASE_NAME)
        # shutil.rmtree(TEMP_DIR)
        # shutil.rmtree(FILES_DIR)
        pass



    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # TESTS
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_public_fields(self):
        """ public_fields """
        # Check that public fields describes in the model are same that in TU.
        # If you broke this test, you probably have to update TU, documentation and wiki...
        self.assertEqual(Job.public_fields, TU_PUBLIC_FIELDS)


    def test_from_id(self):
        """ from_id """
        self.assertEqual(Job.from_id(0), None)
        j = Job.from_id(2)
        self.assertIsInstance(j, Job)
        self.assertEqual(j.name, "J2")


    def test_from_ids(self):
        """ from_ids """
        self.assertEqual(Job.from_ids([]), [])
        j = Job.from_ids([2,15415, 1])
        self.assertIsInstance(j, list)
        self.assertEqual(len(j), 2)
        self.assertIsInstance(j[0], Job)
        self.assertIsInstance(j[1], Job)
        self.assertEqual(j[0].id, 1)
        self.assertEqual(j[1].id, 2)


    def test_load_depth(self):
        """ init & load_depth """
        j = Job.from_id(1, 1)
        self.assertIsInstance(j.inputs, list)
        self.assertIsInstance(j.outputs, list)
        self.assertEqual(len(j.inputs), len(j.inputs_ids))
        self.assertEqual(len(j.outputs), len(j.outputs_ids))
        self.assertIsInstance(j.inputs[0], File)
        self.assertIsInstance(j.outputs[0], File)
        self.assertEqual(j.inputs[0].id, j.inputs_ids[0])
        self.assertEqual(j.outputs[0].id, j.outputs_ids[0])


    def test_to_json(self):
        """ to_json """
        # Test export with default fields
        f = Job.from_id(1, 1)
        j = f.to_json()
        self.assertEqual(len(j), len(TU_PUBLIC_FIELDS))
        json.dumps(j)

        # Test export with only requested fields
        j = f.to_json(["id", "config", "status", "inputs_ids"])
        self.assertEqual(len(j), 4)
        json.dumps(j)

        # Test export with depth loading
        j = f.to_json(["id", "name", "inputs_ids", "inputs"])
        self.assertEqual(len(j), 4)
        self.assertEqual(j["inputs_ids"][0], 3)
        self.assertEqual(f.inputs[0].status, "checked")
        self.assertEqual(j["inputs"][0]["status"], "checked")


    def test_CRUD(self):
        """ CRUD """
        # CREATE
        total = Job.count()
        j1 = Job.new()
        self.assertEqual(Job.count(), total + 1)
        self.assertNotEqual(j1.id, None)
        # UPDATE
        j1.name = "TestJob"
        j1.save()
        # READ
        j2 = Job.from_id(j1.id)
        self.assertEqual(j2.name, "TestJob")
        self.assertEqual(j2.create_date, j1.create_date)
        update1 = j2.update_date
        # UPDATE loading
        j2.load({
            "name" : "FinalJob", 
            "pipeline_id" : 2, 
            "config" : {"param1" : 1, "param2" : [1,2,3]},
            "status" : "finalizing",
            "progress_value" : 0.9,
            "progress_label" : "90%",
            "inputs_ids" : [1,2],
            "outputs_ids" : [3]
            })
        self.assertNotEqual(update1, j2.update_date)
        self.assertEqual(j2.name,"FinalJob")
        self.assertEqual(j2.pipeline_id,2)

        self.assertEqual(j2.config["param2"][1], 2)
        self.assertEqual(j2.status,"finalizing")
        self.assertEqual(j2.progress_value, 0.9)
        self.assertEqual(j2.progress_label, "90%")
        self.assertEqual(j2.inputs_ids, [1,2])
        self.assertEqual(j2.outputs_ids, [3])
        # READ
        j3 = Job.from_id(j1.id, 1)
        self.assertEqual(j3.status,"finalizing")
        self.assertEqual(j3.progress_value, 0.9)
        self.assertEqual(j3.progress_label, "90%")
        self.assertEqual(j3.inputs_ids, [1,2])
        self.assertEqual(j3.outputs_ids, [3])
        self.assertEqual(j2.update_date, j3.update_date)
        # DELETE
        Job.delete(j3.id)
        j4 = Job.from_id(j3.id)
        self.assertEqual(j4, None)
        self.assertEqual(Job.count(), total)