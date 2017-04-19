#!env/python3
# coding: utf-8
import ipdb

import os
# import json
# import datetime
# import uuid
# import psycopg2
# import hashlib
# import asyncio
# import ped_parser

import config as C
import core.model as Model
from core.framework import log, err, array_merge, RegovarException, Timer, run_until_complete









class Core:
    def __init__(self):
        self.users = UserManager()

    def notify_all(self, msg):
        print (msg)

    def user_authentication(self, login, pwd):
        return Model.User.from_credential(login, pwd);




# =====================================================================================================================
# Users MANAGER
# =====================================================================================================================


class UserManager:
    def __init__(self):
        pass




    def get(self, fields=None, query=None, order=None, offset=None, limit=None):
        """
            Generic method to get users data according to provided filtering options
        """
        if fields is None:
            fields = Model.User.public_fields
        if query is None:
            query = {}
        if order is None:
            order = ['lastname', "firstname"]
        if offset is None:
            offset = 0
        if limit is None:
            limit = offset + C.RANGE_MAX

        result = []
        sql = "SELECT " + ','.join(fields) + " FROM \"user\""
        for s in Model.execute(sql):
            entry = {}
            for f in fields:
                entry.update({f: eval("s." + f)})
            result.append(entry)
        return result






















# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

regovar = Core()
log('Regovar core initialised. Server ready !')