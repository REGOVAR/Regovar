#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp
import datetime
import time


from aiohttp import web

from config import *
from core.framework.common import *
from core.framework.tus import *
from core.model import *
from core.core import core
from api_rest.rest import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# PHENOTYPE HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class PhenotypeHandler:

    @user_role('Authenticated')
    def list(self, request):
        """
            Return all phenotypes entries
        """
        return rest_success(core.phenotypes.list())



    @user_role('Authenticated')
    def get(self, request):
        """
            Return all data available for the requested phenotype
        """
        hpo_id = request.match_info.get('hpo_id', None)

        try:
            hpo = core.phenotypes.get(hpo_id)
        except Exception as ex:
            return rest_error('Error occured', ex)
        return rest_success(hpo)


    @user_role('Authenticated')
    async def search(self, request):
        """
            Return all data available phenotype that match the search terms
        """
        data = await request.json()
        if isinstance(data, str): data = json.loads(data)
        search = data["search"] if "search" in data else None
        
        try:
            hpo = core.phenotypes.search(search)
        except Exception as ex:
            return rest_error('Error occured', ex)
        return rest_success(hpo)
 
