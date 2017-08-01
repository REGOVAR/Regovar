#!python
# coding: utf-8


import os
import sys
import shutil
import unittest
import json
import time
import datetime

from config import DATABASE_NAME
from core.model import *



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TEST PARAMETER / CONSTANTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
TU_PUBLIC_FIELDS = ["id", "identifiant", "firstname", "lastname", "sex", "comment", "birthday", "deathday", "update_date", "jobs_ids", "samples_ids", "files_ids", "analyses_ids", "jobs", "samples", "analyses", "files", "indicators", "users", "projects_ids", "projects"]








class TestModelSubject(unittest.TestCase):
    """ MODEL Unit Tests : Subject """

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # PREPARATION
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    @classmethod
    def setUpClass(self):
        # Before test we check that we are doing test on a "safe" database
        if DATABASE_NAME[-5:] != "_test": raise Exception("Wrong config database used")

    @classmethod
    def tearDownClass(self):
        pass



    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # TESTS
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_public_fields(self):
        """ public_fields """
        # Check that public fields describes in the model are same that in TU.
        # If you broke this test, you probably have to update TU, documentation and wiki...
        self.assertEqual(Subject.public_fields, TU_PUBLIC_FIELDS)


    def test_from_id(self):
        """ from_id """
        self.assertEqual(Subject.from_id(0), None)
        s = Subject.from_id(2)
        self.assertIsInstance(s, Subject)
        self.assertEqual(s.identifiant, "S2")


    def test_from_ids(self):
        """ from_ids """
        self.assertEqual(Subject.from_ids([]), [])
        s = Subject.from_ids([3,15415,1])
        self.assertIsInstance(s, list)
        self.assertEqual(len(s), 2)
        self.assertIsInstance(s[0], Subject)
        self.assertIsInstance(s[1], Subject)
        self.assertEqual(s[0].id, 1)
        self.assertEqual(s[1].id, 3)

    def test_load_depth(self):
        """ init & load_depth """
        s = Subject.from_id(1, 1)
        # Check properties
        self.assertEqual(s.id, 1)
        self.assertEqual(s.identifiant, "S1")
        self.assertEqual(s.firstname, "firstname1")
        self.assertEqual(s.lastname, "lastname1")
        self.assertEqual(s.sex, "male")
        self.assertIsInstance(s.jobs_ids, list)
        self.assertEqual(len(s.jobs_ids), 1)
        self.assertIsInstance(s.analyses_ids, list)
        self.assertEqual(len(s.analyses_ids), 0)
        self.assertIsInstance(s.files_ids, list)
        self.assertEqual(len(s.files_ids), 2)
        self.assertIsInstance(s.samples_ids, list)
        self.assertEqual(len(s.samples_ids), 1)
        self.assertIsInstance(s.projects_ids, list)
        self.assertEqual(len(s.projects_ids), 1)
        self.assertIsInstance(s.indicators, list)
        self.assertEqual(len(s.indicators), 1)
        self.assertIsInstance(s.indicators[0], SubjectIndicator)
        self.assertEqual(s.indicators[0].indicator_id, 1)
        self.assertEqual(s.indicators[0].indicator_value_id, 3)
        self.assertIsInstance(s.users, list)
        self.assertEqual(len(s.users), 2)
        self.assertEqual(s.users[0]["id"], 3)
        # Check "depth loaded" properties
        self.assertIsInstance(s.jobs, list)
        self.assertEqual(len(s.jobs), 1)
        self.assertEqual(s.jobs[0].id, 1)
        self.assertIsInstance(s.analyses, list)
        self.assertEqual(len(s.analyses), 0)
        self.assertIsInstance(s.files, list)
        self.assertEqual(len(s.files), 2)
        self.assertIsInstance(s.files[0], File)
        self.assertEqual(s.files[0].id, 1)
        self.assertEqual(len(s.samples), 1)
        self.assertIsInstance(s.samples[0], Sample)
        self.assertEqual(s.samples[0].id, 1)
        self.assertEqual(len(s.projects), 1)
        self.assertIsInstance(s.projects[0], Project)
        self.assertEqual(s.projects[0].id, 6)
        
        
        
    def test_to_json(self):
        """ to_json """
        # Test export with all fields
        s = Subject.from_id(1, 1)
        j = s.to_json()
        self.assertEqual(len(j), len(TU_PUBLIC_FIELDS))
        json.dumps(j)

        # Test export with only requested fields
        j = s.to_json(["id", "identifiant", "projects", "indicators", "samples", "wrong_field"])
        self.assertEqual(len(j), 5)
        json.dumps(j)
        self.assertEqual(j["samples"][0]["id"], 1)
        self.assertEqual(j["projects"][0]["name"], "P1")


    def test_count(self):
        """ count """
        self.assertEqual(Subject.count(), 3)
        

    def test_CRUD(self):
        """ CRUD """
        # CREATE
        total = Subject.count()
        o1 = Subject.new()
        self.assertEqual(Subject.count(), total + 1)
        self.assertNotEqual(o1.id, None)
        # UPDATE
        o1.identifiant = "S4"
        o1.save()
        # READ
        o2 = Subject.from_id(o1.id)
        self.assertEqual(o2, o1)
        # UPDATE loading
        birth = datetime.datetime.now()
        o2.load({
            "identifiant" : "S4.1", 
            "comment" : "comment S4", 
            "birthday" : birth,
            "files_ids" : [1,2]
        })
        self.assertEqual(o2.identifiant,"S4.1")
        self.assertEqual(o2.comment,"comment S4")
        self.assertEqual(o2.birthday, birth)
        self.assertEqual(o2.files_ids, [1,2])
        self.assertEqual(o2.files, [])
        # READ
        o2.init(1, True)
        self.assertEqual(o2.files_ids, [1,2])
        self.assertEqual(len(o2.files), 2)
        self.assertIsInstance(o2.files[0], File)
        self.assertEqual(o2.files[0].id, 1)
        # DELETE
        Subject.delete(o1.id)
        o3 = Subject.from_id(o1.id)
        self.assertEqual(o3, None)
        self.assertEqual(Subject.count(), total)
        
        
        
        
    def test_indicator_management(self):
        """ Indicator management """
        self.skipTest('TODO')
        
        
    def test_user_management(self):
        """ User sharing management """
        # READ
        # - read only access
        self.assertEqual(UserSubjectSharing.get_auth(1,4), False)
        # - no access
        self.assertEqual(UserSubjectSharing.get_auth(1,1), None)
        # - Read/Write access
        self.assertEqual(UserSubjectSharing.get_auth(1,3), True)
        
        # CREATE / UPDATE
        UserSubjectSharing.set(1, 3, False) # update one
        UserSubjectSharing.set(2, 1, True)  # new one
        self.assertEqual(UserSubjectSharing.get_auth(1,3), False)
        self.assertEqual(UserSubjectSharing.get_auth(2,1), True)
        s1 = Subject.from_id(2)
        user = User.from_id(1,1)
        self.assertEqual(len(s1.users), 3)
        self.assertEqual(s1.users[0]["id"], 3)
        self.assertEqual(s1.users[0]["write_authorisation"], True)
        user = User.from_id(1,1)
        self.assertEqual(len(user.subjects_ids), 1)
        self.assertEqual(user.subjects_ids, [2])
        # DELETE
        UserSubjectSharing.unset(2, 1)
        s1.init(1, True)
        user.init(1, True)
        self.assertEqual(len(s1.users), 2)
        self.assertEqual(len(user.subjects_ids), 0)
        
        
    def test_file_management(self):
        """ File management """
        self.skipTest('TODO')
        
        
    def test_project_management(self):
        """ Project management """
        self.skipTest('TODO')
        
        
        
        
        
        
        
        
        
        
        
        