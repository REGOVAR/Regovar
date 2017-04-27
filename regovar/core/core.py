#!env/python3
# coding: utf-8
import ipdb

import os
import json
# import datetime
# import uuid
# import psycopg2
# import hashlib
# import asyncio
# import ped_parser

import config as C
import core.model as Model
from core.framework import log, err, array_merge, RegovarException, Timer, run_until_complete

# import managers
from core.managers.user_manager import UserManager
from core.managers.project_manager import ProjectManager
























# =====================================================================================================================
# CORE MAIN OBJECT
# =====================================================================================================================

class Core:
    def __init__(self):
        self.users = UserManager()
        self.projects = ProjectManager()

    def notify_all(self, msg):
        print (msg)

    def user_authentication(self, login, pwd):
        return Model.User.from_credential(login, pwd);














# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

regovar = Core()
log('Regovar core initialised. Server ready !')