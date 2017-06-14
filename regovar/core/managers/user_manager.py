#!env/python3
# coding: utf-8
import ipdb
import json
import core.model as Model
from core.framework.common import *
from core.framework.erreurs_list import ERR





class UserManager:

    def __init__(self):
        pass



    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
        """
            Generic method to get users data according to provided filtering options
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {}
        if order is None:
            order = "lastname"
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        s = Model.session()
        users = s.query(Model.User).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for u in users: u.init(depth)
        return users




    def delete(self, user_to_delete_id, admin_id):
        """ 
            Retrieve users
        """
        admin = Model.User.from_id(admin_id)
        user = Model.User.from_id(user_to_delete_id)

        if admin is None or "Administration" not in admin.roles_dic.keys() or admin.roles_dic["Administration"] != "Write" :
            raise RegovarException(ERR.E101003, "E101003")
        if user is None:
            raise RegovarException(ERR.E101001, "E101001")
        if admin_id == user_to_delete_id:
            raise RegovarException(ERR.E101004, "E101004")
            
        Model.execute("DELETE FROM \"user\" WHERE id={}".format(user_to_delete_id))
        # core.log_event("Delete user {} {} ({})".format(user.firstname, user.lastname, user.login), user_id=0, type="info")




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