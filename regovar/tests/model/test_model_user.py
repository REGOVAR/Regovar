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
TU_PUBLIC_FIELDS = ["id", "firstname", "lastname", "login", "email", "function", "location", "update_date", "create_date", "settings", "roles", "projects_ids", "subjects_ids", "sandbox_id", "sandbox", "projects", "subjects"]




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
        self.assertEqual(User.public_fields, TU_PUBLIC_FIELDS)


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
        u = User.from_id(3, 1)
        # Check properties
        self.assertEqual(u.id, 3)
        self.assertEqual(u.login, "U3")
        self.assertEqual(u.email, "user3@email.com")
        self.assertEqual(u.firstname, "firstname3")
        self.assertEqual(u.lastname, "lastname3")
        self.assertEqual(u.function, "f3")
        self.assertEqual(u.location, "l3")
        self.assertIsInstance(u.settings, dict)
        self.assertEqual(u.settings["fullscreen"], True)
        self.assertIsInstance(u.roles, dict)
        self.assertEqual(len(u.roles.keys()), 0)
        self.assertEqual(u.is_activated, True)
        self.assertEqual(u.sandbox_id, 3)
        self.assertIsInstance(u.projects_ids, list)
        self.assertEqual(len(u.projects_ids), 2)
        self.assertEqual(u.projects_ids, [6, 7])
        self.assertIsInstance(u.subjects_ids, list)
        self.assertEqual(len(u.subjects_ids), 2)
        self.assertEqual(u.subjects_ids, [1, 2])
        # Check "depth loaded" properties
        self.assertIsInstance(u.sandbox, Project)
        self.assertEqual(u.sandbox.id, 3)
        self.assertIsInstance(u.projects, list)
        self.assertEqual(len(u.projects), 2)
        self.assertIsInstance(u.projects[0], Project)
        self.assertEqual(u.projects[0].id, 6)
        self.assertIsInstance(u.subjects, list)
        self.assertEqual(len(u.subjects), 2)
        self.assertIsInstance(u.subjects[0], Subject)
        self.assertEqual(u.subjects[0].id, 1)
        
        
        

    def test_to_json(self):
        """ to_json """
        # Test export with default fields
        u = User.from_id(4, 1)
        j = u.to_json()
        self.assertEqual(len(j), len(TU_PUBLIC_FIELDS))
        json.dumps(j)

        # Test export with only requested fields
        j = u.to_json(["id", "login", "firstname", "roles", "wrong_field"])
        self.assertEqual(len(j), 4)
        json.dumps(j)

        # Test export with depth loading
        j = u.to_json(["id", "login", "projects", "roles"])
        self.assertEqual(len(j), 4)
        self.assertEqual(j["projects"][0]['indicators'][0]['indicator_id'], 1)
        self.assertEqual(j["roles"], {})


    def test_CRUD(self):
        """ CRUD """
        # CREATE
        total = User.count()
        o1 = User.new("MyLogin")
        self.assertEqual(User.count(), total + 1)
        self.assertNotEqual(o1.id, None)
        self.assertEqual(o1.login, "MyLogin")
        # UPDATE
        o1.login = "TestUser"
        o1.save()
        # READ
        o2 = User.from_id(o1.id)
        self.assertEqual(o2.login, "TestUser")
        self.assertEqual(o2.create_date, o1.create_date)
        update1 = o2.update_date
        # UPDATE loading
        o2.load({
            "login" : "FinalUser", 
            "roles" : {"Administrator": "Write"}, 
            "password" : "toto"
            })
        self.assertNotEqual(update1, o2.update_date)
        self.assertEqual(o2.login,"FinalUser")
        self.assertEqual(o2.roles["Administrator"], "Write")
        o2b = User.from_credential("FinalUser", "toto")
        self.assertEqual(User.from_credential("FinalUser", "Bad pwd"), None)
        self.assertEqual(o2b.id, o2.id)
        # READ
        o3 = User.from_id(o1.id, 1)
        self.assertEqual(o3.login,"FinalUser")
        self.assertEqual(o3.roles["Administrator"], "Write")
        self.assertEqual(o2.update_date, o3.update_date)
        # DELETE
        User.delete(o3.id)
        o4 = User.from_id(o3.id)
        self.assertEqual(o4, None)
        self.assertEqual(User.count(), total)







