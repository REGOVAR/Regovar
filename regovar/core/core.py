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
# Users MANAGER
# =====================================================================================================================


class UserManager:
    def __init__(self):
        pass



    def get(self, fields=None, query=None, sort=None, offset=None, limit=None):
        """
            Generic method to get users data according to provided filtering options
        """
        # Check parameters
        fields, query, sort, offset, limit = check_generic_query_parameter(Model.User.public_fields, ['lastname', "firstname"], fields, query, sort, offset, limit)

        # Build query
        result = []
        sql = "SELECT " + ','.join(fields) + " FROM \"user\""

        # Get result
        rsql = Model.execute(sql)

        # Get and return result
        for s in rsql:
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
        """ 
            Retrieve users
        """
        admin = Model.User.from_id(admin_id)
        user = Model.User.from_id(user_to_delete_id)

        if admin is None or "Administration" not in admin.roles_dic.keys() or admin.roles_dic["Administration"] != "Write" :
            raise RegovarException(ERR.E101003, "E101003")
        if user is None:
            raise RegovarException(ERR.E101004, "E101004")
        if admin_id == user_to_delete_id:
            raise RegovarException(ERR.E101005, "E101005")
            
        Model.execute("DELETE FROM \"user\" WHERE id={}".format(user_to_delete_id))
        # regovar.log_event("Delete user {} {} ({})".format(user.firstname, user.lastname, user.login), user_id=0, type="info")


    def create_or_update(self, user_data, remote_user_id):
        """
            Create or update an user with provided data.
            Creation can be done only by administrator user.
            Admin can edit all user, normal users can only edit themself
        """
        remote_user = Model.User.from_id(remote_user_id)
        if remote_user is None or not isinstance(user_data, dict):
            raise RegovarException(ERR.E101002, "E101002")
        user_id = None
        if "id" in user_data.keys():
            user_id = user_data["id"]
        if remote_user.is_admin() or user_id == remote_user.id:
            user = Model.User.from_id(user_id) or Model.User()
            if "login" in user_data.keys() : user.login = user_data["login"]
            if "firstname" in user_data.keys() : user.firstname = user_data["firstname"]
            if "lastname" in user_data.keys() : user.lastname = user_data["lastname"]
            if "email" in user_data.keys() : user.email = user_data["email"]
            if "function" in user_data.keys() : user.function = user_data["function"]
            if "location" in user_data.keys() : user.location = user_data["location"]
            # Todo : save file in statics assets directory (remove old avatar if necessary), and store new url into db
            #if "avatar" in user_data.keys() : user.avatar = user_data["avatar"]
            if "password" in user_data.keys() : user.erase_password(user_data["password"])
            user.save()
            return user
        return None





















# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

regovar = Core()
log('Regovar core initialised. Server ready !')