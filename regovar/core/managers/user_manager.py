#!env/python3
# coding: utf-8
import ipdb
import json
import core.model as Model
from config import *
from core.framework.common import *
from core.framework.postgresql import execute





class UserManager:

    def list(self):
        """
            List all users with minimal data
        """
        sql = "SELECT id, login, firstname, lastname, email, create_date, update_date, is_activated, is_admin, function, location FROM \"user\" ORDER BY lastname, firstname, id"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "login": res.login,
                "firstname": res.firstname,
                "lastname": res.lastname,
                "email": res.email,
                "is_activated": res.is_activated,
                "is_admin": res.is_admin,
                "function": res.function,
                "location": res.location,
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat()
            })
        return result


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
        s = Model.Session()
        users = s.query(Model.User).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for u in users: u.init(depth)
        return users




    def delete(self, user_to_delete_id, admin_id):
        """ 
            Retrieve users
        """
        admin = Model.User.from_id(admin_id)
        user = Model.User.from_id(user_to_delete_id)

        if admin is None or not admin.is_admin():
            raise RegovarException(code="E101003")
        if user is None:
            raise RegovarException(code="E101001")
        if admin_id == user_to_delete_id:
            raise RegovarException(code="E101004")
            
        Model.User.delete(user_to_delete_id)
        # core.log_event("Delete user {} {} ({})".format(user.firstname, user.lastname, user.login), user_id=0, type="info")




    def create_or_update(self, user_data, remote_user_id):
        """
            Create or update an user with provided data.
            Creation can be done only by administrator user.
            Admin can edit all user, normal users can only edit themself
        """
        remote_user = Model.User.from_id(remote_user_id)
        if remote_user is None or not isinstance(user_data, dict):
            raise RegovarException(code="E101002")
        user_id = None
        if "id" in user_data.keys():
            user_id = user_data["id"]
        if remote_user.is_admin() or user_id == remote_user.id:
            user = Model.User.from_id(user_id) or Model.User.new()
            user.load(user_data)
            # Todo : save file in statics assets directory (remove old avatar if necessary), and store new url into db
            #if "avatar" in user_data.keys() : user.avatar = user_data["avatar"]
            
            user.save()
            return user
        return None
    
    
    