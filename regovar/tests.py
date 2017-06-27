#!python
# coding: utf-8

import unittest
import os



# Pirus part tests
from tests.model.test_model_user import *
from tests.model.test_model_project import *
from tests.model.test_model_subject import *
from tests.model.test_model_file import *
from tests.model.test_model_job import *
from tests.model.test_model_pipeline import *
from tests.core.test_core_filemanager import *
from tests.core.test_core_pipelinemanager import *
from tests.core.test_core_jobmanager import *
from tests.core.test_core_lxdmanager import *
# Annso part tests

# Regovar part tests


from tests.pretty_print import ColourTextTestRunner



# /!\ For a weird raison, unittest.main() doesn't work (no UT loaded) when we import the core object. So we run the tests manually

# Run tests
if __name__ == '__main__':

    print("=====\nTEST MODEL :")
    suiteModel = unittest.TestSuite()
    

    print("-----\nLoading tests :")


    # Load test to execute
    for test in [m for m in TestModelUser.__dict__.keys() if str.startswith(m, "test_")]:
        suiteModel.addTest(TestModelUser(test))
        
    for test in [m for m in TestModelProject.__dict__.keys() if str.startswith(m, "test_")]:
        suiteModel.addTest(TestModelProject(test))
        
    for test in [m for m in TestModelSubject.__dict__.keys() if str.startswith(m, "test_")]:
        suiteModel.addTest(TestModelSubject(test))

    for test in [m for m in TestModelFile.__dict__.keys() if str.startswith(m, "test_")]:
        suiteModel.addTest(TestModelFile(test))

    for test in [m for m in TestModelJob.__dict__.keys() if str.startswith(m, "test_")]:
        suiteModel.addTest(TestModelJob(test))

    for test in [m for m in TestModelPipeline.__dict__.keys() if str.startswith(m, "test_")]:
        suiteModel.addTest(TestModelPipeline(test))

    print("Done\n-----\nRunning tests :")
    runner = ColourTextTestRunner(verbosity=2)
    runner.run(suiteModel)
    
    
    #print("=====\nTEST CORE :")
    #suiteCore = unittest.TestSuite()
    

    #print("-----\nLoading tests :")
    #for test in [m for m in TestCoreFileManager.__dict__.keys() if str.startswith(m, "test_")]:
        #suiteCore.addTest(TestCoreFileManager(test))

    #for test in [m for m in TestCorePipelineManager.__dict__.keys() if str.startswith(m, "test_")]:
        #suiteCore.addTest(TestCorePipelineManager(test))

    #for test in [m for m in TestCoreJobManager.__dict__.keys() if str.startswith(m, "test_")]:
        #suiteCore.addTest(TestCoreJobManager(test))

    ## Need Lxd image on the server to work.
    #if os.path.exists(TestCoreLxdManager.IMAGE_FILE_PATH):
        #tests = [m for m in TestCoreLxdManager.__dict__.keys() if str.startswith(m, "test_")]
        #tests.sort()
        #for test in tests: 
            #suiteCore.addTest(TestCoreLxdManager(test))
    #else:
        #print("WARNING : LXD Manager TU disabled. (because lxd image \"{}\" not available)".format(TestCoreLxdManager.IMAGE_FILE_PATH))

    #print("Done\n=====\nRunning tests :")
    #runner = ColourTextTestRunner(verbosity=2)
    #runner.run(suiteCore)
    
