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
import inspect
from aiohttp import web, MultiDict
from urllib.parse import parse_qsl

from config import *
import core.model as Model
from core.core import regovar
from core.framework import *
# from web.tus import *








# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# COMMON TOOLS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

def rest_success(response_data=None, pagination_data=None):
    """ 
        Build the REST success response that will encapsulate the given data (in python dictionary format)
        :param response_data:   The data to wrap in the JSON success response
        :param pagination_data: The data regarding the pagination
    """
    if response_data is None:
        results = {"success":True}
    else:
        results = {"success":True, "data":response_data}
    if pagination_data is not None:
        results.update(pagination_data)
    return web.json_response(results)



def rest_error(message:str="Unknow error", code:str="", error_id:str=""):
    """ 
        Build the REST error response
        :param message:         The short "friendly user" error message
        :param code:            The code of the error type
        :param error_id:        The id of the error, to return to the end-user. 
                                This code will allow admins to find in logs where exactly this error occure
    """
    results = {
        "success":      False, 
        "msg":          message, 
        "error_code":   code, 
        "error_url":    ERROR_ROOT_URL + code,
        "error_id":     error_id
    }
    return web.json_response(results)


def rest_exception(exception):
    """ 
        Build the REST error response from a RegovarException
    """
    if isinstance(exception, RegovarException):
        return rest_error(exception.msg, exception.code, exception.id)
    else:
        uid = str(uuid.uuid4())
        err("ERROR [{}] {}".format(uid, exception.arg))
        return rest_error("Not managed exception : {}".format(exception.arg), "", uid) 




def user_role(role):
    '''
        Decorator that checks if a user has been authenticated and have the good authorisation.
    '''
    def wrapper(f):
        @functools.wraps(f)
        async def wrapped(self, request):
            has_perm = await permits(request, role)
            if not has_perm:
                message = 'User has no role {}'.format(role)
                raise web.HTTPForbidden(body=message.encode())
            if inspect.iscoroutinefunction(f):
                return await f(self, request)
            else:
                return f(self, request)
        return wrapped
    return wrapper




def notify_all(data):
    msg = json.dumps(data)
    if 'msg' not in data.keys() or data['msg'] != 'hello':
        log ("API_rest Notify All: {0}".format(msg))
    for ws in WebsocketHandler.socket_list:
        ws[0].send_str(msg)

# Give to the core the delegate to call to notify all users via websockets
regovar.notify_all = notify_all






# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# MISC HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class ApiHandler:
    def __init__(self):
        pass

    def welcom(self, request):
        return rest_success({
            "api_url": HOST_P,
            "title": "Regovar Service API",
            "version": "alpha",
            "format_supported": ["json"],
            "website" : "regovar.org"
        })



    def config(self, request):
        return rest_success({
            "host": HOST_P,
            "pagination_default_range": RANGE_DEFAULT,
            "pagination_max_range": RANGE_MAX,
            "export_modules": annso.export_modules, 
            "import_modules": annso.import_modules,
            "report_modules": annso.report_modules
            })



class WebsocketHandler:
    socket_list = []
    async def get(self, request):
        peername = request.transport.get_extra_info('peername')
        if peername is not None:
            host, port = peername

        ws_id = "{}:{}".format(host, port)
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        WebsocketHandler.socket_list.append((ws, ws_id))
        msg = {'msg':'hello', 'data': [[str(_ws[1]) for _ws in WebsocketHandler.socket_list]]}
        notify_all(msg)

        try:
            async for msg in ws:
                if msg.tp == aiohttp.MsgType.text:
                    if msg.data == 'close':
                        log ('CLOSE MESSAGE RECEIVED')
                        await ws.close()
                    else:
                        # Analyse message sent by client and send response if needed
                        data = msg.json()
                        if data['msg'] == 'user_info':
                            log('WebsocketHandler {0} '.format(data['msg']))
                            pass
                        elif msg.tp == aiohttp.MsgType.error:
                            log('ws connection closed with exception {0}'.format(ws.exception()))
        finally:
            WebsocketHandler.socket_list.remove((ws, ws_id))

        return ws



async def on_shutdown(app):
    log("SHUTDOWN SERVER... CLOSE ALL")
    for ws in WebsocketHandler.socket_list:
        await ws[0].close(code=999, message='Server shutdown')



 



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# USER HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class UserHandler:
    '''
        This handler manage all queries about user management and authentication
    '''
    def __init__(self):
        pass
    

    def all(self, request):
        ''' 
            Public method that return the list of regovar's users (only public details).
        '''
        return rest_success(regovar.users.get())


    def get(self, request):
        # FIXME : implement method
        return rest_success("todo get")


    @user_role('Administration:Write')
    async def add(self, request):
        '''
            Add a new user in database. 
            Only available for administrator
        '''
        remote_user_id = await authorized_userid(request)
        user_data = await self.get_user_data_from_request(request)
        try:
            user = regovar.users.create_or_update(user_data, remote_user_id)
        except Exception as err:
            return rest_exception(err)
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
            user = regovar.users.create_or_update(user_data, remote_user_id)
        except Exception as err:
            return rest_exception(err)
        return rest_success(user.to_json())


    async def login(self, request):
        params = await request.post()
        login = params.get('login', None)
        pwd = params.get('password', "")
        print ("{} {}".format(login, pwd))
        user = regovar.user_authentication(login, pwd)
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
            regovar.users.delete(user_to_delete_id, remote_user_id)
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