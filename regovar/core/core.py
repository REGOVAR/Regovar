#!env/python3
# coding: utf-8
import os
from importlib import import_module

import config as C
from core.framework.common import *
from core.model import *
from core.managers import *




#
# The version of the source code
#
REGOVAR_DB_VERSION = "6"         # Used only by the core to know if compatible with current Regovar DB schema
REGOVAR_CORE_VERSION = "0.8.0"   # Official version of the Regovar Server (used client side to know if client compatible with this server)




# =====================================================================================================================
# CORE MAIN OBJECT
# =====================================================================================================================
def default_notify_all(data):
    """
        Default delegate used by the core for notification.
    """
    print(str(data))


class Core:
    version = REGOVAR_CORE_VERSION
    db_version = REGOVAR_DB_VERSION
    
    
    def __init__(self):
        # Check that db major version is compatible with application version
        db_version = execute("SELECT value FROM parameter WHERE key='database_version'").first()[0]
        if db_version.split(".")[0] != REGOVAR_DB_VERSION:
            raise RegovarException("The database version ({}) is not complient with the regovar application source code ({}).".format(db_version, REGOVAR_DB_VERSION))
        else:
            log("DB version check success: {}".format(db_version))
        
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
        self.panels = PanelManager()
        # Regovar Part (User, project, SLI management)
        self.users = UserManager()
        self.projects = ProjectManager()
        self.events = EventManager()
        self.subjects = SubjectManager()
        self.search = SearchManager()
        self.admin = AdminManager()
        
        # Notify all method
        # according to api that will be pluged on the core, this method should be overriden 
        # (See how api_rest override this method in api_rest/rest.py)
        self.notify_all = default_notify_all

        # module loaded dynamicaly as this part of the server should be heavily customisable. 
        # Even is there is bug in these module, the server shall works. but the wrong module is unvailable
        # TODO: manage dynamic reload of modules for better user/sysadmin experience
        self.exporters = {}
        self.reporters = {}
        self.load_export_managers()
        self.load_report_managers()


    def notify_all(self, data):
        """
            Default delegate used by the core for notification.
            according to api that will be pluged on the core, this method should be overriden 
            (See how api_rest override this method in api_rest/rest.py)
        """
        print(str(data))
    

    def user_authentication(self, login, pwd):
        """
            Return the User if credential match.
        """
        return User.from_credential(login, pwd);



    def load_export_managers(self):
        """
            Dynamicaly load export module
        """
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



    def load_report_managers(self):
        """
            Dynamicaly load report module
        """
        # TODO: clean/unload former reporters if self.reporters is not empty
        self.reporters = {}
        # Get modules
        path = "core/managers/reports/"
        mods = [f.split(".")[0] for f in os.listdir(path) if not (f.startswith("__") or f.startswith("abstract_"))]
        
        for m in mods:
            try:
                mod = import_module(path.replace("/", ".") + m)            
            except Exception as ex:
                err("Unable to load report module: {}".format(path.replace("/", ".") + m), ex)
                mod = None
            if mod:
                data = mod.Report.metadata
                if data["name"] in self.exporters.keys():
                    err("Report Manager with the same name ({}) already loaded. Skip.".format(data["name"]))
                else:
                    data.update({"mod": mod.Report})
                    self.reporters[data["name"]] = data
        return self.reporters
            
            
            
            
            




# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

core = Core()
log('Regovar core initialised. Server ready !')

