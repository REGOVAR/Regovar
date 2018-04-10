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
            Return all phenotypes (minimal info) matching the search term
            To be used for autocomplete search by example
        """
        # TODO: escape search
        if not isinstance(search, str) or search.strip() == "":
            raise RegovarException("Invalid search query")
        query = "SELECT DISTINCT hpo_id, label FROM hpo_phenotype WHERE label ILIKE '%{0}%' ORDER BY label LIMIT 100".format(search)
        
        result = []
        for row in execute(query):
            result.append({"id": row.hpo_id, "label": row.label})

        # Search also among synonyms if needed
        if len(result) == 0:
            query = "SELECT DISTINCT hpo_id, label FROM hpo_phenotype WHERE search ILIKE '%{0}%' ORDER BY label LIMIT 100".format(search)
            for row in execute(query):
                result.append({"id": row.hpo_id, "label": row.label})

        # Search also among description if needed
        if len(result) == 0:
            query = "SELECT DISTINCT hpo_id, label FROM hpo_phenotype WHERE description ILIKE '%{0}%' ORDER BY label LIMIT 100".format(search)
            for row in execute(query):
                result.append({"id": row.hpo_id, "label": row.label})

        return result



    def get(self, token):
        """
            Return all phenotypics information (disease and associated gene) for the requested id
            id can be hpo (HP:000000), omim (OMIM:000000), orphanet (ORPHA:000000) or a gene name
        """
        result = None
        if token.startswith("HP:"):
            result = self._get_hp(token)
        elif token.startswith("OMIM:"):
            result = self._get_omim(token)
        elif token.startswith("ORPHA:"):
            result = self._get_orpha(token)
        else:
            result = self._get_gene(token)
        return result










    def _get_hp(self, hpo_id):
        """
            Internal method, called by get(token) to retrieve phenotypics data from a provided hpo id
        """
        sql = "SELECT hpo_id, label, definition, parent, childs, allsubs_diseases, allsubs_genes, meta FROM hpo_phenotype WHERE hpo_id='{}'".format(hpo_id)
        row = execute(sql).first()
        result = {
            "id": hpo_id,
            "type" : "phenotype",
            "label": row.label,
            "definition": row.definition,
            "parent": None,
            "childs": [],
            "diseases": row.allsubs_diseases,
            "genes": row.allsubs_genes,
            "meta": row.meta
        }

        # Related phenotypes
        rel = ["'{}'".format(row.parent)] if row.parent else []
        rel += ["'{}'".format(i) for i in row.childs] if row.childs is not None else []
        sql = "SELECT hpo_id, label FROM hpo_phenotype WHERE hpo_id IN ({}) ORDER BY label".format(",".join(rel))
        for r in execute(sql):
            if r.hpo_id == row.parent:
                result["parent"] = {"id": r.hpo_id, "label": r.label}
            else:
                result["childs"].append({"id": r.hpo_id, "label": r.label})

        return result



    def _get_omim(self, omim_id):
        """
            Internal method, called by get(token) to retrieve disease data from a provided omim id
        """
        omim = omim_id.split(':')[1]
        omim = get_cached_url("https://api.omim.org/api/entry?mimNumber={}&include=all".format(omim), "omim_",  headers={"Accept": "application/json", "apiKey": OMIM_API_KEY})
        result = omim["omim"]["entryList"][0]["entry"]
        
        # result = {
        #     "id": omim_id,
        #     "type" : "disease",
        #     "label": row.label,
        #     "definition": row.definition,
        #     "parent": None,
        #     "childs": [],
        #     "phenotypes": [],
        #     "genes": []
        # }
        return result


    def _get_orpha(self, orpha_id):
        """
            Internal method, called by get(token) to retrieve disease data from a provided orpha id
        """
        result = {
            "id": orpha_id,
            "type" : "disease",
            "label": "",
            "definition": "",
            "parent": None,
            "childs": [],
            "phenotypes": [],
            "genes": []
        }
        return result


    def _get_gene(self, gname):
        """
            Internal method, called by get(token) to retrieve disease data from a provided gene name
        """
        from core.core import core
        return core.search.fetch_gene(gname)



