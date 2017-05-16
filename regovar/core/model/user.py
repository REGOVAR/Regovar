#!env/python3
# coding: utf-8
import os
import json


from core.framework.common import *
from core.framework.postgresql import *
from passlib.hash import pbkdf2_sha256




def user_init(self, loading_depth=0):
    """
        If loading_depth is > 0, children objects will be loaded. Max depth level is 2.
        Children objects of a file are :
            - job_source : set with a Job object if the file have been created by a job. 
            - jobs       : the list of jobs in which the file is used or created
        If loading_depth == 0, children objects are not loaded
    """
    try:
        self.roles_dic = json.loads(self.roles)
    except:
        self.roles_dic = {}


def user_from_id(user_id, loading_depth=0):
    """
        Retrieve user with the provided id in the database
    """
    user = session().query(User).filter_by(id=user_id).first()
    user.init()
    return user


def user_from_ids(user_ids, loading_depth=0):
    """
        Retrieve files corresponding to the list of provided id
    """
    users = []
    if user_ids and len(user_ids) > 0:
        users = session().query(User).filter(User.id.in_(user_ids)).all()
        for u in users:
            u.init(loading_depth)
    return users


def user_from_credential(login, pwd):
    """
        Retrieve File with the provided login+pwd in the database
    """
    user = session().query(User).filter_by(login=login).first()
    if user:
        user.init()
        if user.password is None:
            # Can occur if user created without password
            return user
        if pbkdf2_sha256.verify(pwd, user.password):
            return user
    return None


def user_to_json(self, fields=None):
    """
        Export the user into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = User.public_fields
    for f in fields:
        if f == "creation_date" or f == "update_date":
            result.update({f: eval("self." + f + ".ctime()")})
        else:
            result.update({f: eval("self." + f)})
    return result


def user_set_password(self, old, new):
    """
        This method must be used to set the password of a user
        Return True if the password have be changed, False otherwise
    """
    if (old == None and user.password == None) or pbkdf2_sha256.verify(old, user.password):
        self.password = pbkdf2_sha256.encrypt(new, rounds=200000, salt_size=16)
        self.save()
        return True
    return False


def user_erase_password(self, new):
    """
        Method that erase password with a new one when we forgot the former one.
    """
    self.password = pbkdf2_sha256.encrypt(new, rounds=200000, salt_size=16)
    self.save()
    return True


def user_is_admin(self):
    """
        Return True if user have administration rights; False otherwise
    """
    return isinstance(self, User) and isinstance(self.roles_dic, dict) and "Administration" in self.roles_dic.keys() and self.roles_dic["Administration"] == "Write"


User = Base.classes.user
User.public_fields = ["id", "firstname", "lastname", "login", "email", "function", "location", "last_activity", "settings", "roles"]
User.from_id = user_from_id
User.from_credential = user_from_credential
User.to_json = user_to_json
User.set_password = user_set_password
User.erase_password = user_erase_password
User.is_admin = user_is_admin
User.save = generic_save
User.init = user_init