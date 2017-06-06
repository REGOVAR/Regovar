#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp

import aiohttp_jinja2
import tarfile
import datetime
import time
import uuid
import subprocess


from aiohttp import web, MultiDict
from urllib.parse import parse_qsl


from config import *








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
    if pagination_data:
        results.update(pagination_data)
    return web.json_response(results)



def rest_error(message:str="Unknow", code:str="0", error_id:str=""):
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
        "error_url":    code,
        "error_id":     error_id
    }
    return web.json_response(results)





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
        order = "name"
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
 
