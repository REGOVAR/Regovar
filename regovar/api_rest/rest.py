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
from core.framework.common import *
from core.core import core








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
        err("ERROR [{}] {}".format(uid, exception.args))
        raise exception
        return rest_error("Not managed exception : {}".format(exception.args), "", uid) 




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




def notify_all(self, data):
    msg = json.dumps(data)
    if 'action' not in data.keys() or data['action'] != 'hello':
        log ("API_rest Notify All: {0}".format(msg))
    for ws in WebsocketHandler.socket_list:
        ws[0].send_str(msg)

# Give to the core the delegate to call to notify all users via websockets
core.notify_all = notify_all








def get_query_parameters(query_string, fields_to_retrieve):
    get_params = MultiDict(parse_qsl(query_string))
    result = {}
    for key in fields_to_retrieve:
        value = get_params.get(key, None)
        result.update({key: value})
    return result;






def process_generic_get(query_string, allowed_fields):
        # 1- retrieve query parameters
        get_params = MultiDict(parse_qsl(query_string))
        r_range  = get_params.get('range', "0-" + str(RANGE_DEFAULT))
        r_fields = get_params.get('fields', None)
        r_order  = get_params.get('order_by', None)
        r_sort   = get_params.get('order_sort', None)
        r_filter = get_params.get('filter', None)

        # 2- fields to extract
        fields = allowed_fields
        if r_fields is not None:
            fields = []
            for f in r_fields.split(','):
                f = f.strip().lower()
                if f in allowed_fields:
                    fields.append(f)
        if len(fields) == 0:
            return rest_error("No valid fields provided : " + get_params.get('fields'))

        # 3- Build json query for mongoengine
        query = {}
        if r_filter is not None:
            query = {"$or" : []}
            for k in fields:
                query["$or"].append({k : {'$regex': r_filter}})

        # 4- Order
        order = None
        # if r_sort is not None and r_order is not None:
        #     r_sort = r_sort.split(',')
        #     r_order = r_order.split(',')
        #     if len(r_sort) == len(r_order):
        #         order = []
        #         for i in range(0, len(r_sort)):
        #             f = r_sort[i].strip().lower()
        #             if f in allowed_fields:
        #                 if r_order[i] == "desc":
        #                     f = "-" + f
        #                 order.append(f)
        # order = tuple(order)

        # 5- limit
        r_range = r_range.split("-")
        offset=0
        limit=RANGE_DEFAULT
        try:
            offset = int(r_range[0])
            limit = int(r_range[1])
        except:
            return rest_error("No valid range provided : " + get_params.get('range') )

        # 6- Return processed data
        return fields, query, order, offset, limit




















# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# WEBSOCKET HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
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
        msg = {'action':'hello', 'data': [[str(_ws[1]) for _ws in WebsocketHandler.socket_list]]}
        notify_all(None, msg)

        try:
            async for msg in ws:
                if msg.tp == aiohttp.MsgType.text:
                    if msg.data == 'close':
                        log ('CLOSE MESSAGE RECEIVED')
                        await ws.close()
                    else:
                        # Analyse message sent by client and send response if needed
                        data = msg.json()
                        if data['action'] == 'user_info':
                            log('WebsocketHandler {0} '.format(data['action']))
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
 
