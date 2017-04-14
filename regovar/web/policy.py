#!env/python3
# coding: utf-8
import ipdb; 
from aiohttp_security.abc import AbstractAuthorizationPolicy
import asyncio




class RegovarAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self):
        pass


    async def authorized_userid(self, identity):
        await asyncio.sleep(0)
        return identity


    async def permits(self, identity, permission, context=None):
        await asyncio.sleep(0)
        return True

