#!env/python3
# coding: utf-8
import ipdb; 
from aiohttp_security.abc import AbstractAuthorizationPolicy
import asyncio



from core.model import *


class RegovarAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self):
        pass


    async def authorized_userid(self, identity):
        await asyncio.sleep(0)

        return identity


    async def permits(self, identity, permission, context=None):
        # TODO : check user authorisation 
        await asyncio.sleep(0)
        user = User.from_id(identity)
        if user:
            if permission == 'Authenticated':
                return True

            
            print ("Check authent [{}] for {} ({})".format(permission, user.login, user.roles_dic))
            print ("TODO")
        return False

