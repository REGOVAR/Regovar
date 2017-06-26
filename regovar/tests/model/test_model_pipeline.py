#!python
# coding: utf-8


import os
import sys
import shutil
import unittest
import json
import datetime

from config import DATABASE_NAME
from core.model import *



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TEST PARAMETER / CONSTANTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
TU_PIRUS_PIPELINE_PUBLIC_FIELDS = ["id", "name", "type", "status", "description", "developers", "installation_date", "version", "pirus_api", "image_file_id", "image_file", "manifest", "documents", "path", "jobs_ids", "jobs"]





class TestModelPipeline(unittest.TestCase):
    """ MODEL Unit Tests : Pipeline """

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
        self.assertEqual(Pipeline.public_fields, TU_PIRUS_PIPELINE_PUBLIC_FIELDS)


    def test_from_id(self):
        """ from_id """
        self.assertEqual(Pipeline.from_id(0), None)
        p = Pipeline.from_id(1)
        self.assertIsInstance(p, Pipeline)
        self.assertEqual(p.name, "P1")


    def test_from_ids(self):
        """ from_ids """
        self.assertEqual(Pipeline.from_ids([]), [])
        p = Pipeline.from_ids([2,15415, 1])
        self.assertIsInstance(p, list)
        self.assertEqual(len(p), 2)
        self.assertIsInstance(p[0], Pipeline)
        self.assertIsInstance(p[1], Pipeline)
        self.assertEqual(p[0].id, 1)
        self.assertEqual(p[1].id, 2)


    def test_load_depth(self):
        """ init & load_depth """
        p = Pipeline.from_id(1, 1)
        self.assertIsInstance(p.image_file, File)
        self.assertEqual(p.image_file.id, 1)


    def test_to_json(self):
        """ to_json """
        # Test export with default fields
        p = Pipeline.from_id(1, 1)
        j = p.to_json()
        self.assertEqual(len(j), 12)
        json.dumps(j)

        # Test export with only requested fields
        j = p.to_json(["id", "status", "jobs_ids"])
        self.assertEqual(len(j), 3)
        json.dumps(j)

        # Test export with depth loading
        j = p.to_json(["id", "status", "jobs"])
        self.assertEqual(len(j), 3)
        self.assertEqual(j["jobs"][0]["id"], 1)
        self.assertEqual(j["jobs"][1]["progress_value"], 0.5)



    def test_CRUD(self):
        """ CRUD """
        # CREATE
        total = Pipeline.count()
        p1 = Pipeline.new()
        self.assertEqual(Pipeline.count(), total + 1)
        self.assertNotEqual(p1.id, None)
        # UPDATE
        p1.name = "TestPipeline"
        p1.save()
        pid = p1.id
        # READ
        p2 = Pipeline.from_id(pid)
        self.assertEqual(p2.name, "TestPipeline")
        self.assertEqual(p2.installation_date, p1.installation_date)
        # UPDATE loading
        v = datetime.datetime.now().ctime()
        p2.load({
            "name" : "FinalPipeline", 
            "type" : "lxd", 
            "status" : "ready",
            "description" : "Pipeline Description",
            "developers" : "['Tata', 'Titi']",
            "version" : v,
            "pirus_api" : "v1",
            "image_file_id" : 1,
            "manifest" : '{"param1" : 1, "param2" : [1,2,3]}',
            "documents" : '["/pipeline/form.json", "/pipeline/icon.png"]'
            })
        self.assertEqual(p2.name,"FinalPipeline")
        self.assertEqual(p2.type,"lxd")
        self.assertEqual(p2.status,"ready")
        self.assertEqual(p2.description,"Pipeline Description")
        self.assertEqual(p2.developers,"['Tata', 'Titi']")
        self.assertEqual(p2.version, v)
        self.assertEqual(p2.pirus_api,"v1")
        self.assertEqual(p2.image_file_id,1)
        configjson = json.loads(p2.manifest)
        self.assertEqual(configjson["param2"][1], 2)
        documents = json.loads(p2.documents)
        self.assertEqual("/pipeline/form.json" in p2.documents, True)
        # READ
        p3 = Pipeline.from_id(pid, 1)
        self.assertEqual(p3.status,"ready")
        self.assertEqual(p3.image_file_id, 1)
        # DELETE
        Pipeline.delete(pid)
        p4 = Pipeline.from_id(pid)
        self.assertEqual(p4, None)
        self.assertEqual(Pipeline.count(), total)