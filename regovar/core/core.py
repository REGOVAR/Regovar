#!env/python3
# coding: utf-8
import ipdb
import os
from importlib import import_module

import config as C
from core.framework.common import *
from core.model import *
from core.managers import *










# =====================================================================================================================
# CORE MAIN OBJECT
# =====================================================================================================================
def notify_all_print(self, data):
    """
        Default delegate used by the core for notification.
    """
    print(str(data))


class Core:
    def __init__(self):
        # Pipeline and job management (Pirus part)
        self.files = FileManager()
        self.pipelines = PipelineManager()
        self.jobs = JobManager()
        self.container_managers = {}
        self.container_managers["lxd"] = LxdManager()
        # Annotations and variant management (Annso part)
        self.analyses = AnalysisManager()
        self.samples = SampleManager()
        self.annotations = AnnotationManager()
        self.filters = FilterEngine()
        self.phenotypes = PhenotypeManager()
        # Regovar Part (User, project, SLI management)
        self.users = UserManager()
        self.projects = ProjectManager()
        self.events = EventManager()
        self.subjects = SubjectManager()
        self.search = SearchManager()
        self.admin = AdminManager()


        # method handler to notify all
        # according to api that will be pluged on the core, this method should be overriden 
        # to really do a notification. (See how api_rest override this method)
        self.notify_all = notify_all_print

        # module loaded dynamicaly as this part of the server should be heavily customisable. 
        # Even is there is bug in these module, the server shall works. but the wrong module is unvailable
        # TODO: manage dynamic reload of modules for better user/sysadmin experience
        self.exporters = {}
        self.reporters = {}
        self.importers = {}
        self.load_export_managers()



    def user_authentication(self, login, pwd):
        """
            Return the User if credential match.
        """
        return User.from_credential(login, pwd);



    def load_export_managers(self):
        # TODO: clean/unload former exporters if self.exporters is not empty
        self.exporters = {}
        # Get modules
        path = "core/managers/exports/"
        mods = [f.split(".")[0] for f in os.listdir(path) if not (f.startswith("__") or f.startswith("abstract_"))]
        
        for m in mods:
            try:
                mod = import_module(path.replace("/", ".") + m)            
            except Exception as ex:
                err("Unable to load export module: {}".format(path.replace("/", ".") + m), ex)
                mod = None
            if mod:
                data = mod.Exporter.metadata
                if data["name"] in self.exporters.keys():
                    err("Export Manager with the same name ({}) already loaded. Skip.".format(data["name"]))
                else:
                    data.update({"mod": mod.Exporter})
                    self.exporters[data["name"]] = data
        return self.exporters
            




# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

core = Core()
log('Regovar core initialised. Server ready !')

