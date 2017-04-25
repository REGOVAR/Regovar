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
                if f == "roles" or f == "settings":
                    data = eval("s." + f)
                    if data:
                        entry.update({f: json.loads(eval("s." + f))})
                    else:
                        entry.update({f: None})
                else:
                    entry.update({f: eval("s." + f)})
            result.append(entry)
        return result



    def delete(self, user_to_delete_id, admin_id):
        # retrieve users
        admin = Model.User.from_id(admin_id)
        user = Model.User.from_id(user_to_delete_id)

        if admin is None or "Administration" not in admin.roles_dic.keys() or admin.roles_dic["Administration"] != "Write" :
            raise RegovarException("User deletion need to be done by an admin")
        if user is None:
            raise RegovarException("User to delete doesn't exits")
        if admin_id == user_to_delete_id:
            raise RegovarException("Enable to delete yourself. This action must be done by another admin.")
            
        Model.execute("DELETE FROM \"user\" WHERE id={}".format(user_to_delete_id))
        # regovar.log_event("Delete user {} {} ({})".format(user.firstname, user.lastname, user.login), user_id=0, type="info")




















# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

regovar = Core()
log('Regovar core initialised. Server ready !')