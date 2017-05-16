#!env/python3
# coding: utf-8
import ipdb


import config as C
from core.framework.common import *
from core.model import *

# import managers
from core.pirus import *
from core.regovar import *










# =====================================================================================================================
# CORE MAIN OBJECT
# =====================================================================================================================
def notify_all_print(msg):
    """
        Default delegate used by the core for notification.
    """
    print(str(msg))


class Core:
    def __init__(self):
        # Pirus Part
        self.files = FileManager()
        self.pipelines = PipelineManager()
        self.jobs = JobManager()
        self.container_managers = {}
        # Load Container managers
        self.container_managers["lxd"] = LxdManager()

        # Regovar Part
        self.users = UserManager()
        self.projects = ProjectManager()



        # method handler to notify all
        # according to api that will be pluged on the core, this method should be overriden 
        # to really do a notification. (See how api_rest override this method)
        self.notify_all = notify_all_print




    def user_authentication(self, login, pwd):
        """
            FIXME : why directly in the core ?
        """
        return User.from_credential(login, pwd);









# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

core = Core()
log('Regovar core initialised. Server ready !')