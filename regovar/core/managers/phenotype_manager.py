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
from core.framework.postgresql import execute
from core.model import *



# =====================================================================================================================
# Phenotype MANAGER
# =====================================================================================================================


class PhenotypeManager:
    def __init__(self):
        pass


    def list(self):
        """
            Return all phenotypes entries
        """
        sql = "WITH data AS (SELECT DISTINCT(hpo_id) AS id, hpo_label AS label FROM hpo_phenotype UNION SELECT DISTINCT(hpo_id) AS id, hpo_label AS label FROM hpo_disease)  SELECT distinct(id), label FROM data;" 
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "label": res.label
            })
        return result

    
    def search(self, search):
        """
            Return all phenotypes matching the search term
        """
        # TODO: escape search
        if not isinstance(search, str) or search.strip() == "":
            raise RegovarException("Invalid search query")
        query = "SELECT DISTINCT hpo_id, hpo_label FROM hpo_phenotype WHERE hpo_label ILIKE '%{0}%' ORDER BY hpo_label LIMIT 100".format(search)
        
        result = []
        for row in execute(query):
            result.append({"id": row.hpo_id, "label": row.hpo_label})
        return result


    
    def search_disease(self, search):
        """
            Return all disease matching the search term
        """
        # TODO: escape search
        if not isinstance(search, str) or search.strip() == "":
            raise RegovarException("Invalid search query")
        query = "SELECT disease_id, array_agg(gene_name) as genes, max(hpo_label) as label FROM hpo_disease WHERE hpo_label ILIKE '%{0}%' GROUP BY disease_id ORDER BY label LIMIT 100".format(search)
        
        result = []
        for row in execute(query):
            result.append({"id": row.disease_id, "label": row.label, "genes": row.genes})
        return result



    def get(self, token):
        """
            Return all phenotypics information (disease and associated gene) for the requested id
            id can be hpo (HP:000000), omim (OMIM:000000), orphanet (ORPHA:000000) or a gene name
        """
        result = {
            "hpo_id": token,
            "label": "",
            "diseases": {}
        }
        
        if token.startswith("HP:"):
            query = "SELECT disease_id, string_agg(gene_name, ', ') as genes, max(hpo_label) as label FROM hpo_disease WHERE hpo_id='{0}' GROUP BY disease_id".format(token)
            for row in execute(query):
                result["label"] = row.label
                if row.disease_id in result["diseases"]:
                    result["diseases"][row.disease_id].append(row.genes)
                else:
                    result["diseases"][row.disease_id] = [row.genes]
        elif token.startswith("OMIM:"): #or hpo_id.startswith("ORPHA:"):
            # Get omim data
            omim = token.split(':')[1]
            omim = get_cached_url("https://api.omim.org/api/entry?mimNumber={}&include=all".format(omim), "omim_",  headers={"Accept": "application/json", "apiKey": OMIM_API_KEY})
            result = omim["omim"]["entryList"][0]["entry"]
            
        else:
            # we supposed that it's a gene name
            result = {"diseases": [], "phenotypes": []}
            query = "SELECT distinct disease_id FROM hpo_disease WHERE gene_name='{0}' ORDER BY disease_id".format(token)
            for row in execute(query):
                result["diseases"].append({"id": row.disease_id})
            query = "SELECT distinct hpo_id, hpo_label FROM hpo_phenotype WHERE gene_name ILIKE '%{}%' ORDER BY hpo_label".format(token)
            for row in execute(query):
                result["phenotypes"].append({"id": row.hpo_id, "label": row.hpo_label})
            
        return result







