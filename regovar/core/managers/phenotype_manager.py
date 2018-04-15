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
        elif token.startswith("OMIM:") or token.startswith("ORPHA:") or token.startswith("DECIPHER:"):
            result = self._get_disease(token)
            if token.startswith("OMIM:"):
                result.update(self._get_omim(token))
            elif token.startswith("ORPHA:"):
                result.update(self._get_orpha(token))
            elif token.startswith("DECIPHER:"):
                result.update(self._get_decipher(token))
        else:
            result = self._get_gene(token)
        return result










    def _get_hp(self, hpo_id):
        """
            Internal method, called by get(token) to retrieve phenotypics data from a provided hpo id
        """
        sql = "SELECT hpo_id, label, definition, parents, childs, allsubs_diseases, allsubs_genes, category, meta FROM hpo_phenotype WHERE hpo_id='{}'".format(hpo_id)
        row = execute(sql).first()
        result = {
            "id": hpo_id,
            "type" : "phenotypic",
            "label": row.label,
            "definition": row.definition,
            "parents": [],
            "childs": [],
            "diseases": [],
            "genes": row.allsubs_genes,
            "subjects": [],
            "category": row.category,
            "meta": row.meta
        }
        # Related phenotypes
        parents = row.parents if row.parents is not None else []
        childs = row.childs if row.childs is not None else []
        rel = ["'{}'".format(i) for i in parents] 
        rel += ["'{}'".format(i) for i in childs] 
        sql = "SELECT hpo_id, label FROM hpo_phenotype WHERE hpo_id IN ({}) ORDER BY label".format(",".join(rel))
        for r in execute(sql):
            if r.hpo_id in parents:
                result["parents"].append({"id": r.hpo_id, "label": r.label})
            else:
                result["childs"].append({"id": r.hpo_id, "label": r.label})
        # Related diseases
        rel = ["'{}'".format(i) for i in row.allsubs_diseases]
        sql = "SELECT hpo_id, label FROM hpo_disease WHERE hpo_id IN ({}) ORDER BY label".format(",".join(rel))
        for r in execute(sql):
            result["diseases"].append({"id": r.hpo_id, "label": r.label})
        # Related subjects
        sql = "SELECT s.id, s.identifier, s.firstname, s.lastname, s.sex FROM subject s INNER JOIN subject_phenotype p ON p.subject_id=s.id WHERE p.presence='present' AND p.hpo_id='{}'".format(hpo_id)
        for r in execute(sql):
            result["subjects"].append({"id": r.hpo_id, "identifier": r.identifier, "firstname": r.firstname, "lastname": r.lastname, "sex": r.sex})
        
        # Qualifiers phenotypes
        rel = []
        for did in row.meta["qualifiers"]:
            rel += ["'{}'".format(i) for i in row.meta["qualifiers"][did]]
        rel = remove_duplicates(rel)
        if len(rel) > 0:
            sql = "SELECT hpo_id, label, definition FROM hpo_phenotype WHERE hpo_id IN ({})".format(",".join(rel))
            for r in execute(sql):
                p = {"id": r.hpo_id, "label": r.label, "definition": r.definition}
                for did in row.meta["qualifiers"]:
                    if r.hpo_id in row.meta["qualifiers"][did]:
                        row.meta["qualifiers"][did].remove(r.hpo_id)
                        row.meta["qualifiers"][did].append(p)
        return result


    def _get_disease(self, hpo_id):
        """
            Internal method, called by get(token) to retrieve generic disease data from a provided hpo id
        """
        sql = "SELECT hpo_id, label, genes, phenotypes, phenotypes_neg, meta FROM hpo_disease WHERE hpo_id='{}'".format(hpo_id)
        row = execute(sql).first()
        result = {
            "id": hpo_id,
            "type" : "disease",
            "label": row.label,
            "genes": row.genes,
            "phenotypes": [],
            "phenotypes_neg": [],
            "meta": row.meta
        }
        # Related phenotypes
        pheno = row.phenotypes if row.phenotypes is not None else []
        npheno = row.phenotypes_neg if row.phenotypes_neg is not None else []
        rel = ["'{}'".format(i) for i in pheno] 
        rel += ["'{}'".format(i) for i in npheno] 
        sql = "SELECT hpo_id, label, definition, meta FROM hpo_phenotype WHERE hpo_id IN ({}) ORDER BY label".format(",".join(rel))
        rel = []
        for r in execute(sql):
            p = {"id": r.hpo_id, "label": r.label, "definition": r.definition}
            if hpo_id in r.meta["qualifiers"]:
                p["qualifiers"] = r.meta["qualifiers"][hpo_id]
                rel += p["qualifiers"]
            if r.hpo_id in pheno:
                result["phenotypes"].append(p)
            else:
                result["phenotypes_neg"].append(p)

        # Qualifiers phenotypes
        rel =remove_duplicates(rel)
        rel.sort()
        rel = ["'{}'".format(p) for p in rel] 
        if len(rel) > 0:
            sql = "SELECT hpo_id, label, definition FROM hpo_phenotype WHERE hpo_id IN ({}) ORDER BY label".format(",".join(rel))
            for r in execute(sql):
                p = {"id": r.hpo_id, "label": r.label, "definition": r.definition}
                for pdata in result["phenotypes"]:
                    if "qualifiers" in pdata and r.hpo_id in pdata["qualifiers"]:
                        pdata["qualifiers"].remove(r.hpo_id)
                        pdata["qualifiers"].append(p)
                for pdata in result["phenotypes_neg"]:
                    if "qualifiers" in pdata and r.hpo_id in pdata["qualifiers"]:
                        pdata["qualifiers"].remove(r.hpo_id)
                        pdata["qualifiers"].append(p)
        return result


    def _get_omim(self, omim_id):
        """
            Internal method, called by get(token) to retrieve disease data from omim
        """
        omim = omim_id.split(':')[1]
        omim = get_cached_url("https://api.omim.org/api/entry?mimNumber={}&include=all".format(omim), "omim_",  headers={"Accept": "application/json", "apiKey": OMIM_API_KEY})
        return {"omim": omim["omim"]["entryList"][0]["entry"]}


    def _get_orpha(self, orpha_id):
        """
            Internal method, called by get(token) to retrieve disease data from a provided orpha id
        """
        # TODO
        return {"orphanet": None}


    def _get_decipher(self, decipher_id):
        """
            Internal method, called by get(token) to retrieve disease data from a provided decipher id
        """
        # TODO
        return {"decipher": None}


    def _get_gene(self, gname):
        """
            Internal method, called by get(token) to retrieve disease data from a provided gene name
        """
        from core.core import core
        return core.search.fetch_gene(gname)



