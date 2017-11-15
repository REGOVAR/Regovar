#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp
import aiohttp_jinja2
import datetime
import time
import re
import requests


from aiohttp import web
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
                - variant :   ILIKE "chr:pos ref>alt" || "chr:pos_start-pos_end" || "chr:pos~delta " || "chr:pos"
                - project :   ILIKE "%name%"
                - analysis :  ILIKE "%name%"
                - sample :    ILIKE "%name%"
                - subject :   ILIKE "%firstname|lastname|identifiant%"
                - file :      ILIKE "%name%"
                - gene :      ILIKE "%name%"
                - phenotype : ILIKE "%name%" | "HP:id" 
                - disease :   ILIKE "%name%" | "OMIM:id" | "ORPHA:id"
                - user :      ILIKE "%login|firstname|lastname%"
                - pipeline :  ILIKE "%name%"
                - panel :     ILIKE "%name%"
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
        disease_res = self.search_disease(searchQuery)
        user_res = self.search_user(searchQuery)
        pipeline_res = self.search_pipeline(searchQuery)
        panel_res = self.search_panel(searchQuery)
        
        result = { 
            "total_result": len(variant_res) + len(project_res) + len(analysis_res) + len(sample_res) + len(subject_res) + len(file_res) + len(gene_res) + len(phenotype_res) + len(disease_res) + len(user_res) + len(pipeline_res) + len(panel_res), 
            "variant":   variant_res,
            "project":   project_res,
            "analysis":  analysis_res,
            "sample":    sample_res,
            "subject":   subject_res,
            "file":      file_res,
            "gene":      gene_res,
            "phenotype": phenotype_res,
            "disease":   disease_res,
            "user":      user_res,
            "pipeline":  pipeline_res,
            "panel":     panel_res
        }

        return rest_success(result)









    def search_variant(self, search):
        """
            Return variant that match the search query
        """
        result = self.search_variant_pattern_1(search)
        if len(result) == 0:
            result = self.search_variant_pattern_2(search)
        if len(result) == 0:
            result = self.search_variant_pattern_3(search)
        if len(result) == 0:
            result = self.search_variant_pattern_4(search)
        return result

    def search_variant_pattern_1(self, search):
        result = []
        pattern = re.compile("chr([0-9,x,y,m]+):([0-9]+) ([a,c,g,t]*)>([a,c,g,t]*)")
        res = pattern.search(search.lower())
        if res:
            # Search variant for all reference
            chrm = res[1]
            pos  = int(res[2])-1
            ref  = res[3].upper()
            alt  = res[4].upper()
            if chrm == "x": chrm = 23
            if chrm == "y": chrm = 24
            if chrm == "m": chrm = 25
            
            query = "SELECT id, sample_list, regovar_score, regovar_score_meta FROM variant_{} WHERE chr={} AND pos={} AND ref='{}' AND alt='{}'"
            for ref_id in core.annotations.ref_list.keys():
                if ref_id > 0:
                    suffix = core.annotations.ref_list[ref_id].lower() # execute("SELECT table_suffix FROM reference WHERE id={}".format(ref_id)).first().table_suffix
                    for row in execute(query.format(suffix, chrm, pos, ref, alt)):
                        result.append({
                            "id": row.id, 
                            "label": "Chr{}:{} {}>{}".format(chrm, pos+1, ref, alt), 
                            "ref_id": ref_id, 
                            "ref_name": core.annotations.ref_list[ref_id],
                            "sample_list": row.sample_list,
                            "regovar_score": row.regovar_score,
                            "regovar_score_meta": row.regovar_score_meta})
        return result
    
    def search_variant_pattern_2(self, search):
        result = []
        pattern = re.compile("chr([0-9,x,y,m]+):([0-9]+)-([0-9]+)")
        res = pattern.search(search.lower())
        if res:
            # Search variant for all reference
            chrm = res[1]
            pos1  = int(res[2])-1
            pos2  = int(res[3])-1
            if chrm == "x": chrm = 23
            if chrm == "y": chrm = 24
            if chrm == "m": chrm = 25
            
            query = "SELECT id, pos, ref, alt, sample_list, regovar_score, regovar_score_meta FROM variant_{} WHERE chr={} AND pos>={} AND pos<={}"
            for ref_id in core.annotations.ref_list.keys():
                if ref_id > 0:
                    suffix = core.annotations.ref_list[ref_id].lower() # execute("SELECT table_suffix FROM reference WHERE id={}".format(ref_id)).first().table_suffix
                    for row in execute(query.format(suffix, chrm, pos1, pos2)):
                        result.append({
                            "id": row.id, 
                            "label": "Chr{}:{} {}>{}".format(chrm, row.pos+1, row.ref, row.alt), 
                            "ref_id": ref_id, 
                            "ref_name": core.annotations.ref_list[ref_id],
                            "sample_list": row.sample_list,
                            "regovar_score": row.regovar_score,
                            "regovar_score_meta": row.regovar_score_meta})
        return result

    def search_variant_pattern_3(self, search):
        result = []
        pattern = re.compile("chr([0-9,x,y,m]+):([0-9]+)~([0-9]+)")
        res = pattern.search(search.lower())
        if res:
            # Search variant for all reference
            chrm  = res[1]
            pos   = int(res[2])-1 
            delta = int(res[3])
            if chrm == "x": chrm = 23
            if chrm == "y": chrm = 24
            if chrm == "m": chrm = 25
            
            query = "SELECT id, pos, ref, alt, sample_list, regovar_score, regovar_score_meta FROM variant_{} WHERE chr={} AND pos>={} AND pos<={}"
            for ref_id in core.annotations.ref_list.keys():
                if ref_id > 0:
                    suffix = core.annotations.ref_list[ref_id].lower() # execute("SELECT table_suffix FROM reference WHERE id={}".format(ref_id)).first().table_suffix
                    for row in execute(query.format(suffix, chrm, pos-delta, pos+delta)):
                        result.append({
                            "id": row.id, 
                            "label": "Chr{}:{} {}>{}".format(chrm, row.pos+1, row.ref, row.alt), 
                            "ref_id": ref_id, 
                            "ref_name": core.annotations.ref_list[ref_id],
                            "sample_list": row.sample_list,
                            "regovar_score": row.regovar_score,
                            "regovar_score_meta": row.regovar_score_meta})
        return result

    def search_variant_pattern_4(self, search):
        result = []
        pattern = re.compile("chr([0-9,x,y,m]+):([0-9]+)")
        res = pattern.search(search.lower())
        if res:
            # Search variant for all reference
            chrm  = res[1]
            pos   = int(res[2])-1
            if chrm == "x": chrm = 23
            if chrm == "y": chrm = 24
            if chrm == "m": chrm = 25
            
            query = "SELECT id, pos, ref, alt, sample_list, regovar_score, regovar_score_meta FROM variant_{} WHERE chr={} AND pos={}"
            for ref_id in core.annotations.ref_list.keys():
                if ref_id > 0:
                    suffix = core.annotations.ref_list[ref_id].lower() # execute("SELECT table_suffix FROM reference WHERE id={}".format(ref_id)).first().table_suffix
                    for row in execute(query.format(suffix, chrm, pos)):
                        result.append({
                            "id": row.id, 
                            "label": "Chr{}:{} {}>{}".format(chrm, row.pos+1, row.ref, row.alt), 
                            "ref_id": ref_id, 
                            "ref_name": core.annotations.ref_list[ref_id],
                            "sample_list": row.sample_list,
                            "regovar_score": row.regovar_score,
                            "regovar_score_meta": row.regovar_score_meta})
        return result



    def search_project(self, search):
        """
            Return projects that match the search query
        """
        result = session().query(Project).filter(Project.name.ilike("%{0}%".format(search))).all()
        for p in result: p.init(0)
        return [p.to_json() for p in result]
    


    def search_analysis(self, search):
        """
            Return analyses that match the search query
        """
        result = session().query(Analysis).filter(Analysis.name.ilike("%{0}%".format(search))).all()
        for res in result: res.init(1)
        fields = Analysis.public_fields + ["project"]
        return [r.to_json(fields) for r in result]
    


    def search_sample(self, search):
        """
            Return samples that match the search query
        """
        result = session().query(Sample).filter(Sample.name.ilike("%{0}%".format(search))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]
    


    def search_subject(self, search):
        """
            Return subjects that match the search query
        """
        result = session().query(Subject).filter(or_(Subject.identifier.ilike("%{0}%".format(search)), Subject.firstname.ilike("%{0}%".format(search)), Subject.lastname.ilike("%{0}%".format(search)))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]
    


    def search_file(self, search):
        """
            Return files that match the search query
        """
        result = session().query(File).filter(File.name.ilike("%{0}%".format(search))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]
    


    def search_gene(self, search):
        """
            Return gene that match the search query
        """
        # TODO: cache
        result = []
        query = "http://rest.genenames.org/search/symbol/{}".format(search)
        data = get_cache(query)
        if not data: 
            res = requests.get(query, headers={"Accept": "application/json"})
            if res.ok:
                data = json.loads(res.content.decode())
                set_cache(query, data)
            else:
                err("EXTERNAL REQUEST failled: " + query)
        
        if data:
            i = 0
            for row in data["response"]["docs"]:
                result.append({"id": row["hgnc_id"], "symbol": row["symbol"]})
                i +=1
                if i == 100: break;
        return result
    


    def search_phenotype(self, search):
        """
            Return phenotype that match the search query
        """
        from core.core import core
        if search.startswith("HP:"):
            return core.phenotypes.get(search)
        else:
            return core.phenotypes.search(search.lower())
    
    

    def search_disease(self, search):
        """
            Return disease that match the search query
        """
        from core.core import core
        if search.startswith("OMIM:") or search.startswith("ORPHA:"):
            return core.phenotypes.get(search)
        # TODO: search disease by name (need to integrate OMIM/ORPHA public data (id<->title) into Regovar database)
        #else:
            #return core.phenotypes.search_disease(query.lower())
        return []
    
    
    
    def search_user(self, search):
        """
            Return user that match the search query
        """
        result = session().query(User).filter(or_(User.login.ilike("%{0}%".format(search)), User.firstname.ilike("%{0}%".format(search)), User.lastname.ilike("%{0}%".format(search)))).all()
        for r in result: r.init(0)
        return [r.to_json() for r in result]



    def search_pipeline(self, search):
        """
            Return pipeline that match the search query
        """
        result = session().query(Pipeline).filter(Pipeline.name.ilike("%{0}%".format(search))).all()
        for p in result: p.init(0)
        return [p.to_json() for p in result]



    def search_panel(self, search):
        """
            Return panel that match the search query
        """
        #result = session().query(Panel).filter(Panel.name.ilike("%{0}%".format(search))).all()
        #for p in result: p.init(0)
        #return [p.to_json() for p in result]
        return []
    

    




    




 
