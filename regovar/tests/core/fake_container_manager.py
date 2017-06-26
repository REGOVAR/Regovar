#!python
# coding: utf-8


import os
from config import JOBS_DIR
from core.managers.containers.abstract_container_manager import AbstractContainerManager


class FakeContainerManager4Test(AbstractContainerManager):
    """
        This test will check that workflow between core, container manager and celery are working as expected.
        This test will not check container managers.
        Note that there are dedicated tests by container manager's type (lxd, github, ...)
    """
    def __init__(self):
        self.need_image_file = True
        self.supported_features = {
            "pause_job" : True,
            "stop_job" : True,
            "monitoring_job" : True
        }
        self.is_installed = False
        self.is_init = False
        self.is_running = False
        self.is_paused = False
        self.is_stoped = False
        self.is_monitoring = False
        self.is_finalized = False



    def install_pipeline(self, pipeline, asynch=False):
        """ Fake installation, success if pipeline's name contains "success"; failed otherwise """
        self.is_installed = "success" in pipeline.name
        return self.is_installed

    def uninstall_pipeline(self, pipeline, asynch=False):
        """ Fake uninstallation, success if pipeline's name contains "success"; failed otherwise """
        self.is_installed = "success" in pipeline.name
        return self.is_installed

    def init_job(self, job, asynch=False, auto_notify=True):
        """ Fake init job : success if job's name contains "success"; failed otherwise """
        self.is_init = True

        return "success" in job.name


    def start_job(self, job, asynch=False):
        """ Fake start job : success if job's name contains "success"; failed otherwise """
        self.is_running = True
        return "success" in job.name


    def pause_job(self, job, asynch=False):
        """ Fake pause job : success if job's name contains "success"; failed otherwise """
        self.is_paused = True
        return "success" in job.name


    def stop_job(self, job, asynch=False):
        """ Fake stop job : success if job's name contains "success"; failed otherwise """
        self.is_stoped = True
        return "success" in job.name

    def monitoring_job(self, job):
        """ Fake stop job : success if job's name contains "success"; failed otherwise """
        self.is_monitoring = True
        return {"monitoring_field" : True}


    def finalize_job(self, job, asynch=False):
        """ Fake finalize job : success if job's name contains "success"; failed otherwise """
        self.is_finalized = True
        return "success" in job.name