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
# Phenotype MANAGER
# =====================================================================================================================


class PhenotypeManager:
    def __init__(self):
        pass

    
    def search(self, search):
        """
            Return all hpo terms matching the search term
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



    def get(self, hpo_id):
        """
            Return all phenotypics information (disease and associated gene) to the hpo terms
        """
        result = []
        
        if hpo_id.startswith("HP:"):
            query = "SELECT disease_id, array_agg(gene_name) as genes, max(hpo_label) as label FROM hpo_disease WHERE hpo_id='{0}' GROUP BY disease_id ORDER BY label".format(hpo_id)
            for row in execute(query):
                result.append({"id": row.disease_id, "label": row.label, "genes": row.genes})
        elif hpo_id.startswith("OMIM:") or hpo_id.startswith("ORPHA:"):
            query = "SELECT DISTINCT hpo_id, hpo_label FROM hpo_disease WHERE disease_id='{0}' ORDER BY hpo_label".format(hpo_id)
            for row in execute(query):
                result.append({"id": row.hpo_id, "label": row.hpo_label})
        else:
            # we supposed that it's a gene name
            result = {"diseases": [], "phenotypes": []}
            query = "SELECT distinct disease_id FROM hpo_disease WHERE gene_name='{0}' ORDER BY disease_id".format(hpo_id)
            for row in execute(query):
                result["diseases"].append({"id": row.disease_id})
            query = "SELECT distinct hpo_id, hpo_label FROM hpo_phenotype WHERE gene_name ILIKE '%{}%' ORDER BY hpo_label".format(hpo_id)
            for row in execute(query):
                result["phenotypes"].append({"id": row.hpo_id, "label": row.hpo_label})
            
        return result







