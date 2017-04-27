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
# TOOLS
# =====================================================================================================================

def check_generic_query_parameter(allowed_fields, default_sort, fields, query, sort, offset, limit):
    """
        Generic method used by the core to check that generic fields/query/sort/offset/limit paramters à good
        fields : list of fields for lazy loading
        query  : dic with for each fields (keys) the list of value
        sort   : list of field on which to sort (prefix by "-" to sort field DESC)
        offset : start offset
        limit  : max number of result to return
    """
    # TODO check param and raise error if wrong parameter : E200001, E200002, E200003, E200004
    if fields is None:
        fields = Model.User.public_fields
    if query is None:
        query = {}
    if sort is None:
        sort = default_sort
    if offset is None:
        offset = 0
    if limit is None:
        limit = C.RANGE_DEFAULT
    return fields, query, sort, offset, limit
















# =====================================================================================================================
# CORE MAIN OBJECT
# =====================================================================================================================

class Core:
    def __init__(self):
        self.users = UserManager()

    def notify_all(self, msg):
        print (msg)

    def user_authentication(self, login, pwd):
        return Model.User.from_credential(login, pwd);














# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

regovar = Core()
log('Regovar core initialised. Server ready !')