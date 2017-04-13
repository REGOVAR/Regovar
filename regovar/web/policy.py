#!env/python3
# coding: utf-8
import ipdb; 
from aiohttp_security.abc import AbstractAuthorizationPolicy




class RegovarAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self):
        pass


    def authorized_userid(self, identity):
        user = regovar.user.from_id(identity)
        if user is not None:
            return True
        return False


    def permits(self, identity, permission, context=None):
        ipdb.set_trace()
        return True

