#!env/python3
# coding: utf-8
import ipdb


import config as C
from core.framework.common import *
from core.model import *
from core.managers import *










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
        # Pirus part (Pipeline and job management)
        self.files = FileManager()
        self.pipelines = PipelineManager()
        self.jobs = JobManager()
        self.container_managers = {}
        self.container_managers["lxd"] = LxdManager()
        # Annso part (Annotations and variant management)
        self.analyses = AnalysisManager()
        self.samples = SampleManager()
        self.variants = VariantManager()
        self.annotations = AnnotationManager()
        # Regovar Part (User, project, SLI management)
        self.users = UserManager()
        self.projects = ProjectManager()
        self.events = EventManager()
        self.subjects = SubjectManager()

        # TODO : import module as Pirus pipeline ?
        self.import_modules = {}
        for name in C.IMPORTS_MODULES:
            try:
                m = __import__('imports.{0}'.format(name))
                self.import_modules[name] = {
                    "info": eval('m.{0}.metadata'.format(name)),
                    "do": eval('m.{0}.import_data'.format(name))}
                self.import_modules[name].update({'id': name})
            except:
                err("Unable to load imports.{0} module".format(name))

        # method handler to notify all
        # according to api that will be pluged on the core, this method should be overriden 
        # to really do a notification. (See how api_rest override this method)
        self.notify_all = notify_all_print




    def user_authentication(self, login, pwd):
        """
            Return the User if credential match.
        """
        return User.from_credential(login, pwd);







# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

core = Core()
log('Regovar core initialised. Server ready !')

