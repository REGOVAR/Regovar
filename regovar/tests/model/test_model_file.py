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
TU_FILE_PUBLIC_FIELDS = ["id", "name", "type", "comment", "path", "size", "upload_offset", "status", "create_date", "update_date", "tags", "md5sum", "job_source_id", "jobs_ids", "job_source", "jobs"]








class TestModelFile(unittest.TestCase):
    """ MODEL Unit Tests : File """

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
        self.assertEqual(File.public_fields, TU_FILE_PUBLIC_FIELDS)


    def test_from_id(self):
        """ from_id """
        self.assertEqual(File.from_id(0), None)
        f = File.from_id(1)
        self.assertIsInstance(f, File)
        self.assertEqual(f.name, "F1.tar.xz")


    def test_from_ids(self):
        """ from_ids """
        self.assertEqual(File.from_ids([]), [])
        f = File.from_ids([3,15415,1])
        self.assertIsInstance(f, list)
        self.assertEqual(len(f), 2)
        self.assertIsInstance(f[0], File)
        self.assertIsInstance(f[1], File)
        self.assertEqual(f[0].id, 1)
        self.assertEqual(f[1].id, 3)

    def test_load_depth(self):
        """ init & load_depth """
        f = File.from_id(4, 1)
        self.assertEqual(len(f.jobs), 1)
        self.assertIsInstance(f.jobs[0], Job)
        self.assertIsInstance(f.job_source, Job)
        self.assertEqual(f.job_source.id, 1)

    def test_to_json(self):
        """ to_json """
        # Test export with default fields
        f = File.from_id(4, 1)
        j = f.to_json()
        self.assertEqual(len(j), 11)
        json.dumps(j)

        # Test export with only requested fields
        j = f.to_json(["id", "name", "type", "job_source_id"])
        self.assertEqual(len(j), 4)
        json.dumps(j)

        # Test export with depth loading
        j = f.to_json(["id", "name", "job_source", "jobs"])
        self.assertEqual(len(j), 4)
        self.assertEqual(j["job_source"]["id"], 1)
        self.assertEqual(j["jobs"][0]["status"], "done")


    def test_CRUD(self):
        """ CRUD """
        # CREATE
        total = File.count()
        f1 = File.new()
        self.assertEqual(File.count(), total + 1)
        self.assertNotEqual(f1.id, None)
        # UPDATE
        f1.name = "TestFile"
        f1.save()
        # READ
        f2 = File.from_id(f1.id)
        self.assertEqual(f2.name, "TestFile")
        self.assertEqual(f2.create_date, f1.create_date)
        update1 = f2.update_date
        # UPDATE loading
        f2.load({
            "name" : "FinalTest", 
            "size" : 123, 
            "upload_offset" : 12,
            "status" : "checked",
            "md5sum" : "md5Final",
            "job_source_id" : 1
            })
        self.assertNotEqual(update1, f2.update_date)
        self.assertEqual(f2.name,"FinalTest")
        self.assertEqual(f2.size,123)
        self.assertEqual(f2.upload_offset,12)
        self.assertEqual(f2.status,"checked")
        self.assertEqual(f2.job_source_id,1)
        # READ
        f3 = File.from_id(f1.id, 1)
        self.assertEqual(f3.name,"FinalTest")
        self.assertEqual(f3.size,123)
        self.assertEqual(f3.upload_offset,12)
        self.assertEqual(f3.status,"checked")
        self.assertEqual(f3.job_source.id, 1)
        self.assertEqual(f2.update_date, f3.update_date)
        # DELETE
        File.delete(f3.id)
        f4 = File.from_id(f3.id)
        self.assertEqual(f4, None)
        self.assertEqual(File.count(), total)
