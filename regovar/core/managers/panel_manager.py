#!env/python3
# coding: utf-8
import ipdb
import json





from config import *
from core.framework.common import *
from core.framework.erreurs_list import ERR
import core.model as Model


class PanelManager:



    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
        """
            Generic method to get panels data according to provided filtering options
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {}
        if order is None:
            order = ["name"]
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        panels = Model.Session().query(Model.Panel).filter_by(**query).order_by(",".join(order)).limit(limit).offset(offset).all()
        for p in panels: p.init(depth)
        return panels




    def delete(self, panel_id):
        """ 
            Delete the panel
        """
        panel = Model.Panel.from_id(panel_id)
        if not panel: raise RegovarException("Unable to delete panel")
        # TODO
        # regovar.log_event("Delete user {} {} ({})".format(user.firstname, user.lastname, user.login), user_id=0, type="info")





    def create_or_update(self, panel_data, loading_depth=1):
        """
            Create or update a panel with provided data.
        """
        if not isinstance(panel_data, dict): raise RegovarException(ERR.E202002, "E202002")

        pid = None
        if "id" in panel_data.keys() and panel_data["id"]:
            pid = panel_data["id"]

        # Get or create the panel
        panel = Model.Panel.from_id(pid, loading_depth) or Model.Panel.new()
        panel.load(panel_data)
        return panel


    def search(self, query):
        """
            search provided query
        """
        # Search gene, phenotype and disease that match the query
        from core.core import core
        gene_res = core.search.search_gene(query)
        phenotype_res = core.search.search_phenotype(query)
        disease_res = core.search.search_disease(query)

        # For diseases and phenotypes, get corresponding gene
        #for pheno in phenotype_res:
            #res = [r.gene_name for r in execute("SELECT DISTINCT gene_name FROM hpo_phenotype WHERE hpo_id='{}'".format(pheno["id"]))]
            #pheno.update({"genes": res})
        #for disease in disease_res:
            #res = [r.gene_name for r in execute("SELECT DISTINCT gene_name FROM hpo_disease WHERE disease_id='{}'".format(pheno["id"]))]
            #disease.update({"genes": res})
        
        # Format result
        result = { 
            "total_result": len(gene_res) + len(phenotype_res) + len (disease_res),
            "gene":      gene_res,
            "phenotype": phenotype_res,
            "disease":   disease_res
        }
        return result

