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
TU_PUBLIC_FIELDS = ["id", "name", "comment", "parent_id", "parent", "is_folder", "create_date", "update_date", "jobs_ids", "files_ids", "analyses_ids", "jobs", "analyses", "files", "indicators", "users", "is_sandbox"]








class TestModelProject(unittest.TestCase):
    """ MODEL Unit Tests : Project """

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
        self.assertEqual(Project.public_fields, TU_PUBLIC_FIELDS)


    def test_from_id(self):
        """ from_id """
        self.assertEqual(Project.from_id(0), None)
        f = Project.from_id(2)
        self.assertIsInstance(f, Project)
        self.assertEqual(f.name, "sandbox U2")


    def test_from_ids(self):
        """ from_ids """
        self.assertEqual(Project.from_ids([]), [])
        f = Project.from_ids([3,15415,1])
        self.assertIsInstance(f, list)
        self.assertEqual(len(f), 2)
        self.assertIsInstance(f[0], Project)
        self.assertIsInstance(f[1], Project)
        self.assertEqual(f[0].id, 1)
        self.assertEqual(f[1].id, 3)

    def test_load_depth(self):
        """ init & load_depth """
        p = Project.from_id(6, 1)
        # Check properties
        self.assertEqual(p.id, 6)
        self.assertEqual(p.name, "P1")
        self.assertEqual(p.comment, "comment")
        self.assertEqual(p.parent_id, 5)
        self.assertEqual(p.is_folder, False)
        self.assertEqual(p.is_sandbox, False)
        self.assertIsInstance(p.jobs_ids, list)
        self.assertEqual(len(p.jobs_ids), 2)
        self.assertIsInstance(p.files_ids, list)
        self.assertEqual(len(p.files_ids), 2)
        self.assertIsInstance(p.analyses_ids, list)
        self.assertEqual(len(p.analyses_ids), 0)
        self.assertIsInstance(p.subjects_ids, list)
        self.assertEqual(len(p.subjects_ids), 2)
        self.assertIsInstance(p.indicators, list)
        self.assertEqual(len(p.indicators), 1)
        self.assertIsInstance(p.indicators[0], ProjectIndicator)
        self.assertEqual(p.indicators[0].indicator_id, 1)
        self.assertEqual(p.indicators[0].indicator_value_id, 3)
        self.assertIsInstance(p.users, list)
        self.assertEqual(len(p.users), 1)
        self.assertEqual(p.users[0]["id"], 3)
        self.assertEqual(p.is_sandbox, False)
        # Check "depth loaded" properties
        self.assertIsInstance(p.jobs, list)
        self.assertEqual(len(p.jobs), 2)
        self.assertIsInstance(p.analyses, list)
        self.assertEqual(len(p.analyses), 0)
        #self.assertIsInstance(p.analyses[0], ProjectIndicator)
        self.assertIsInstance(p.files, list)
        self.assertEqual(len(p.files), 2)
        self.assertIsInstance(p.files[0], File)
        self.assertIsInstance(p.subjects, list)
        self.assertEqual(len(p.subjects), 2)
        self.assertIsInstance(p.subjects[0], Subject)
        self.assertIsInstance(p.parent, Project)
        self.assertEqual(p.parent.is_folder, True)
        
        
        
    def test_to_json(self):
        """ to_json """
        # Test export with all fields
        p = Project.from_id(6, 1)
        j = p.to_json()
        self.assertEqual(len(j), len(TU_PUBLIC_FIELDS))
        json.dumps(j)

        # Test export with only requested fields
        j = p.to_json(["id", "name", "parent", "indicators", "wrong_field"])
        self.assertEqual(len(j), 4)
        json.dumps(j)
        self.assertEqual(j["parent"]["id"], 5)
        self.assertEqual(j["parent"]["name"], "folder")


    def test_count(self):
        """ count """
        self.assertEqual(Project.count(), 2)
        self.assertEqual(Project.count(count_folder=True), 3)
        self.assertEqual(Project.count(count_sandbox=True), 6)
        self.assertEqual(Project.count(True, True), 7)
        

    def test_CRUD(self):
        """ CRUD """
        # CREATE
        total = Project.count()
        o1 = Project.new()
        self.assertEqual(Project.count(), total + 1)
        self.assertNotEqual(o1.id, None)
        # UPDATE
        o1.name = "P3"
        o1.save()
        # READ
        o2 = Project.from_id(o1.id)
        self.assertEqual(o2, o1)

        # UPDATE loading
        o2.load({
            "name" : "P3.1", 
            "comment" : "comment P3", 
            "parent_id" : 5
            })
        self.assertEqual(o2.name,"P3.1")
        self.assertEqual(o2.comment,"comment P3")
        self.assertEqual(o2.parent_id, 5)
        # READ
        o2.init(1, True)
        self.assertEqual(o2.name,"P3.1")
        self.assertEqual(o2.comment, "comment P3")
        self.assertEqual(o2.parent_id, 5)
        self.assertEqual(o2.parent.id , 5)
        # DELETE
        Project.delete(o2.id)
        o3 = Project.from_id(o2.id)
        self.assertEqual(o3, None)
        self.assertEqual(Project.count(), total)
        
        
        
        
    def test_indicator_management(self):
        """ Indicator management """
        self.skipTest('TODO')
        
        
    def test_user_management(self):
        """ User sharing management """
        # READ
        # - read only access
        self.assertEqual(UserProjectSharing.get_auth(6,3), False)
        # - no access
        self.assertEqual(UserProjectSharing.get_auth(4,3), None)
        # - Read/Write access
        self.assertEqual(UserProjectSharing.get_auth(7,3), True)
        
        # CREATE / UPDATE
        UserProjectSharing.set(1, 3, False)
        UserProjectSharing.set(6, 3, True)
        self.assertEqual(UserProjectSharing.get_auth(1,3), False)
        self.assertEqual(UserProjectSharing.get_auth(6,3), True)
        p1 = Project.from_id(1)
        self.assertEqual(len(p1.users), 1)
        self.assertEqual(p1.users[0]["id"], 3)
        self.assertEqual(p1.users[0]["write_authorisation"], False)
        # DELETE
        UserProjectSharing.unset(1, 3)
        p1.init(1, True)
        self.assertEqual(len(p1.users), 0)
        user = User.from_id(3,1)
        self.assertEqual(len(user.projects_ids), 2)
        self.assertEqual(user.projects_ids, [6,7])
        
        
    def test_file_management(self):
        """ File management """
        # READ
        p1 = Project.from_id(6)
        self.assertEqual(p1.files_ids, [1,2])
        # CREATE / UPDATE
        ProjectFile.set(6, 2)
        ProjectFile.set(6, 3)
        p1.init(1, True) #reload object
        self.assertEqual(p1.files_ids, [1,2,3])
        # DELETE
        ProjectFile.unset(6, 2)
        p1.init(1, True) #reload object
        self.assertEqual(p1.files_ids, [1,3])
        
        
        
    def test_subject_management(self):
        """ Subject management """
        self.skipTest('TODO')
        
        
        
        
        
        
        
        
        
        
        
        