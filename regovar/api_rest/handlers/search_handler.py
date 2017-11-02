#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp
import aiohttp_jinja2
import datetime
import time


from aiohttp import web, MultiDict
from urllib.parse import parse_qsl
from sqlalchemy import or_, func


from config import *
from core.framework.common import *
from core.framework.tus import *
from core.model import *
from core.core import core
from api_rest.rest import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# SEARCH HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class SearchHandler:


    def get(self, request):
        """ 
            Search provided query in following "objects" : 
                - variant :   LIKE "chr:pos-ref-alt"
                - project :   LIKE "%name%"
                - analysis :  LIKE "%name%"
                - sample :    LIKE "%name%"
                - subject :   LIKE "%firstname|lastname|identifiant%"
                - file :      LIKE "%name%"
                - gene :      LIKE "%name%"
                - phenotype : LIKE "%name%"
                - user :      LIKE "%login|firstname|lastname%"
                - pipeline :  LIKE "%name%"
                - panel :     LIKE "%name%"
            Return list of matching results
        """
        searchQuery = request.match_info.get('query', None)
        if searchQuery is None :
            return rest_error("Nothing to search...")

        variant_res = self.search_variant(searchQuery)
        project_res = self.search_project(searchQuery)
        analysis_res = self.search_analysis(searchQuery)
        sample_res = self.search_sample(searchQuery)
        subject_res = self.search_subject(searchQuery)
        file_res = self.search_file(searchQuery)
        gene_res = self.search_gene(searchQuery)
        phenotype_res = self.search_phenotype(searchQuery)
        user_res = self.search_user(searchQuery)
        pipeline_res = self.search_pipeline(searchQuery)
        panel_res = self.search_panel(searchQuery)
        
        result = { 
            "total_result": len(variant_res) + len(project_res) + len(analysis_res) + len(sample_res) + len(subject_res) + len(file_res) + len(gene_res) + len(phenotype_res) + len(user_res) + len(pipeline_res) + len(panel_res), 
            "variant":   variant_res,
            "project":   project_res,
            "analysis":  analysis_res,
            "sample":    sample_res,
            "subject":   subject_res,
            "file":      file_res,
            "gene":      gene_res,
            "phenotype": phenotype_res,
            "user":      user_res,
            "pipeline":  pipeline_res,
            "panel":     panel_res
        }

        return rest_success(result)



    def search_variant(self, query):
        """
            Return variant that match the query
        """
        # TODO
        return []



    def search_project(self, query):
        """
            Return projects that match the query
        """
        result = session().query(Project).filter(Project.name.ilike("%{0}%".format(query.lower()))).all()
        for p in result: p.init(0)
        return [p.to_json() for p in result]
    


    def search_analysis(self, query):
        """
            Return analyses that match the query
        """
        result = session().query(Analysis).filter(Analysis.name.ilike("%{0}%".format(query.lower()))).all()
        for res in result: res.init(1)
        fields = Analysis.public_fields + ["project"]
        return [r.to_json(fields) for r in result]
    


    def search_sample(self, query):
        """
            Return samples that match the query
        """
        result = session().query(Sample).filter(Sample.name.ilike("%{0}%".format(query.lower()))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]
    


    def search_subject(self, query):
        """
            Return subjects that match the query
        """
        result = session().query(Subject).filter(or_(Subject.identifier.ilike("%{0}%".format(query.lower())), Subject.firstname.ilike("%{0}%".format(query.lower())), Subject.lastname.ilike("%{0}%".format(query.lower())))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]
    


    def search_file(self, query):
        """
            Return files that match the query
        """
        result = session().query(File).filter(File.name.ilike("%{0}%".format(query.lower()))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]
    


    def search_gene(self, query):
        """
            Return gene that match the query
        """
        # TODO
        return []
    


    def search_phenotype(self, query):
        """
            Return phenotype that match the query
        """
        # TODO
        return []
    


    def search_user(self, query):
        """
            Return user that match the query
        """
        result = session().query(User).filter(or_(User.login.ilike("%{0}%".format(query.lower())), User.firstname.ilike("%{0}%".format(query.lower())), User.lastname.ilike("%{0}%".format(query.lower())))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]



    def search_pipeline(self, query):
        """
            Return pipeline that match the query
        """
        result = session().query(Pipeline).filter(Pipeline.name.ilike("%{0}%".format(query.lower()))).all()
        for p in result: p.init(0)
        return [p.to_json() for p in result]



    def search_panel(self, query):
        """
            Return panel that match the query
        """
        #result = session().query(Panel).filter(Panel.name.like("%{0}%".format(query))).all()
        #for p in result: p.init(0)
        #return [p.to_json() for p in result]
        return []
    

    




    




 
