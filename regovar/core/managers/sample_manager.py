#!env/python3
# coding: utf-8
import ipdb

import os
import json
import datetime
import uuid
import psycopg2
import hashlib
import asyncio
import ped_parser



from config import *
from core.framework.common import *
from core.model import *




# =====================================================================================================================
# Samples MANAGER
# =====================================================================================================================


class SampleManager:
    def __init__(self):
        pass


    def total(self):
        return execute("SELECT count(*) FROM sample").first()[0]


    def get(self, fields=None, query=None, order=None, offset=None, limit=None, sublvl=0):
        """
            Generic method to get files metadata according to provided filtering options
        """
        if fields is None:
            fields = Sample.public_fields
        if query is None:
            query = {}
        if order is None:
            order = ['-create_date', "name"]
        if offset is None:
            offset = 0
        if limit is None:
            limit = offset + RANGE_MAX

        result = []
        for s in execute("SELECT sp.id, sp.name, sp.comments  FROM sample sp"):
            result.append({"id": s[0], "name": s[1], "comments": s[2], "analyses": []})
        return result
 
