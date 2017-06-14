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
            - projects : the list of projects that can access the user
            - sandbox   : the sandbox project of the user
            - 
        If loading_depth == 0, children objects are not loaded
    """
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    # Load acl
    try:
        self.roles_dic = json.loads(self.roles)
    except:
        self.roles_dic = {}
    self.projects_ids = UserProjectSharing.get_projects_ids(self.id)
    self.load_depth(loading_depth)



def user_load_depth(self, loading_depth):
    from core.model.project import Project
    if loading_depth > 0:
        try:
            self.projects = UserProjectSharing.get_projects(self.sandbox_id, self.loading_depth-1)
            self.sandbox = Project.from_id(self.sandbox_id, self.loading_depth-1)
        except Exception as ex:
            raise RegovarException("User data corrupted (id={}).".format(self.id), "", ex)








def user_from_id(user_id, loading_depth=0):
    """
        Retrieve user with the provided id in the database
    """
    user = session().query(User).filter_by(id=user_id).first()
    if user : user.init(loading_depth)
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
        if f == "last_activity":
            result.update({f: eval("self." + f + ".ctime()")})
        elif f == "settings" or f == "roles":
            try:
                result.update({f: json.loads(eval("self." + f ))})
            except Exception as ex:
                war("Unable to serialise user data : {}. {}".format(f, str(ex)))
        elif f == "sandbox":
            if self.loading_depth > 0:
                result.update({"sandbox": self.sandbox.to_json()})
        elif f == "projects":
            if self.loading_depth > 0:
                result.update({"projects": [p.to_json() for p in self.projects]})
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


def user_count():
    """
        Return total of Analyses entries in database
    """
    return generic_count(User)


User = Base.classes.user
User.public_fields = ["id", "firstname", "lastname", "login", "email", "function", "location", "last_activity", "settings", "roles", "projects_ids", "sandbox_id", "sandbox", "projects"]
User.from_id = user_from_id
User.from_credential = user_from_credential
User.to_json = user_to_json
User.set_password = user_set_password
User.erase_password = user_erase_password
User.is_admin = user_is_admin
User.save = generic_save
User.init = user_init
User.load_depth = user_load_depth
User.count = user_count





# =====================================================================================================================
# UserProjectSharing
# =====================================================================================================================


def ups_get_projects_ids(user_id, write_auth=None):
    """
        Return the list of ids of projects that are accessible to the user.
        If write_auth set to None, return both project readonly and writable;
        otherwise return only readonly if false, only writable if true.
    """
    if not write_auth:
        return [p.project_id for p in session().query(UserProjectSharing).filter_by(user_id=user_id).all()]
    else:
        return [p.project_id for p in session().query(UserProjectSharing).filter_by(user_id=user_id, write_authorisation=write_auth).all()]


def ups_get_projects(user_id, write_auth=None, loading_depth=0):
    """
        Return the list of projects that are accessible to the user.
    """
    if not write_auth:
        return [p.init(loading_depth-1) for p in session().query(UserProjectSharing).filter_by(user_id=user_id).all()]
    else:
        return [p.init(loading_depth-1) for p in session().query(UserProjectSharing).filter_by(user_id=user_id, write_authorisation=write_auth).all()]

UserProjectSharing = Base.classes.user_project_sharing
UserProjectSharing.get_projects_ids = ups_get_projects_ids
UserProjectSharing.get_projects = ups_get_projects








