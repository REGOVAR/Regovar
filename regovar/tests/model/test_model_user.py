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
TU_USER_PUBLIC_FIELDS = ["id", "firstname", "lastname", "login", "email", "function", "location", "last_activity", "settings", "roles", "projects_ids", "sandbox_id", "sandbox", "projects"]




class TestModelUser(unittest.TestCase):
    """ MODEL Unit Tests : User """

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
        self.assertEqual(User.public_fields, TU_USER_PUBLIC_FIELDS)


    def test_from_id(self):
        """ from_id """
        self.assertEqual(User.from_id(0), None)
        f = User.from_id(1)
        self.assertIsInstance(f, User)
        self.assertEqual(f.login, "admin")


    def test_from_ids(self):
        """ from_ids """
        self.assertEqual(User.from_ids([]), [])
        u = User.from_ids([3,15415,1])
        self.assertIsInstance(u, list)
        self.assertEqual(len(u), 2)
        self.assertIsInstance(u[0], User)
        self.assertIsInstance(u[1], User)
        self.assertEqual(u[0].id, 1)
        self.assertEqual(u[1].id, 3)

    def test_load_depth(self):
        """ init & load_depth """
        u = User.from_id(2, 1)
        self.assertIsInstance(u.sandbox, Project)
        self.assertEqual(u.sandbox.id, 2)
        self.assertEqual(len(u.projects), 3)
        self.assertIsInstance(u.projects[0], Project)
        self.assertEqual(u.projects[0].id, 4)

    def test_to_json(self):
        """ to_json """
        # Test export with default fields
        f = User.from_id(4, 1)
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
        total = User.count()
        f1 = User.new()
        self.assertEqual(User.count(), total + 1)
        self.assertNotEqual(f1.id, None)
        # UPDATE
        f1.name = "TestFile"
        f1.save()
        # READ
        f2 = User.from_id(f1.id)
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
        f3 = User.from_id(f1.id, 1)
        self.assertEqual(f3.name,"FinalTest")
        self.assertEqual(f3.size,123)
        self.assertEqual(f3.upload_offset,12)
        self.assertEqual(f3.status,"checked")
        self.assertEqual(f3.job_source.id, 1)
        self.assertEqual(f2.update_date, f3.update_date)
        # DELETE
        User.delete(f3.id)
        f4 = User.from_id(f3.id)
        self.assertEqual(f4, None)
        self.assertEqual(User.count(), total)
