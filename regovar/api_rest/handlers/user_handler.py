#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp
import aiohttp_jinja2
import datetime
import time
import uuid

import aiohttp_security
from aiohttp_session import get_session
from aiohttp_security import remember, forget, authorized_userid, permits

import asyncio
import functools
from aiohttp import web
from urllib.parse import parse_qsl

from config import *
from core.framework.common import *
from core.model import *
from core.core import core
from api_rest.rest import *










 



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# USER HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class UserHandler:
    '''
        This handler manage all queries about user management and authentication
    '''
    def __init__(self):
        pass
    

    def list(self, request):
        ''' 
            Public method that return the list of regovar's users (only public details).
        '''
        # Generic processing of the get query
        fields, query, order, offset, limit = process_generic_get(request.query_string, User.public_fields)
        depth = 0
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : User.count(),
            "range_max"    : RANGE_MAX,
        }
        # Return result of the query 
        users = core.users.get(fields, query, order, offset, limit, depth)
        return rest_success([u.to_json() for u in users], range_data)


    @user_role('Authenticated')
    def get(self, request):
        # TODO : manage query parameters for fields
        user_id = request.match_info.get('user_id', 0)
        try:
            user = core.users.get(user_id)
        except Exception as ex:
            return rest_exception(ex)
        return rest_success("todo get")


    @user_role('Administration:Write')
    async def new(self, request):
        '''
            Add a new user in database. 
            Only available for administrator
        '''
        remote_user_id = await authorized_userid(request)
        user_data = await self.get_user_data_from_request(request)
        try:
            user = core.users.create_or_update(user_data, remote_user_id)
        except Exception as ex:
            return rest_exception(ex)
        return rest_success(user.to_json())


    @user_role('Authenticated')
    async def edit(self, request):
        '''
            Edit a user data
            Only available the user on himself, and administrator on all user
        '''
        remote_user_id = await authorized_userid(request)
        user_data = await self.get_user_data_from_request(request)
        user = None
        try:
            user = core.users.create_or_update(user_data, remote_user_id)
        except Exception as ex:
            return rest_exception(ex)
        return rest_success(user.to_json())


    async def login(self, request):
        params = await request.post()
        login = params.get('login', None)
        pwd = params.get('password', "")
        print ("{} {}".format(login, pwd))
        user = core.user_authentication(login, pwd)
        if user:
            # response = rest_success(user.to_json())
            response = rest_success(user.to_json()) # web.HTTPFound('/')
            # Ok, user's credential are correct, remember user for the session
            await remember(request, response, str(user.id))
            return response
        raise web.HTTPForbidden()


    @user_role('Authenticated')
    async def logout(self, request):
        # response = rest_success("Your are disconnected")
        response = web.Response(body=b'You have been logged out')
        await  forget(request, response)
        return response


    @user_role('Administration:Write')
    async def delete(self, request):
        # Check that user is admin, and is not deleting himself (to ensure that there is always at least one admin)
        remote_user_id = await authorized_userid(request)
        user_to_delete_id = request.match_info.get('user_id', -1)
        try:
            core.users.delete(user_to_delete_id, remote_user_id)
        except Exception as err:
            return rest_exception(err)
        return rest_success()


    async def get_user_data_from_request(self, request):
        """
            Tool for this manager to retrieve data from put/post request 
            and build json 
        """
        params = await request.post()
        user_id = request.match_info.get('user_id', 0)
        login = params.get('login', None)
        password = params.get('password', None)
        firstname = params.get('firstname', None)
        lastname = params.get('lastname', None)
        email = params.get('email', None)
        function = params.get('function', None)
        location = params.get('location', None)
        avatar = params.get('avatar', None)

        user = { "id" : user_id }
        if login : user.update({"login" : login})
        if firstname : user.update({"firstname" : firstname})
        if lastname : user.update({"lastname" : lastname})
        if email : user.update({"email" : email})
        if function : user.update({"function" : function})
        if location : user.update({"location" : location})
        if password : user.update({"password" : password})
        if avatar : user.update({"avatar" : avatar})

        return user