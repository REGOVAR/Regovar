#!env/python3
# coding: utf-8
import ipdb
import json





from config import *
from core.framework.common import *
from core.framework.postgresql import execute
import core.model as Model


class PanelManager:


    def list(self):
        """
            List all panels with minimal data
        """
        sql = "SELECT p.id, p.name, p.description, p.owner, p.shared, e.id as vid, e.version, e.comment, e.create_date, e.update_date FROM panel p INNER JOIN panel_entry e ON p.id=e.panel_id ORDER BY p.name, e.update_date"
        result = []
        current = None
        for res in execute(sql): 
            if not current or current["id"] != res.id:
                if current != None: result.append(current)
                current = current = {
                    "id": res.id,
                    "name": res.name,
                    "description": res.description,
                    "owner": res.owner,
                    "shared": res.shared,
                    "create_date": res.create_date.isoformat(),
                    "update_date": res.update_date.isoformat(),
                    "versions": []
                }
            
            current["versions"].append({
                "id": res.vid,
                "name": res.version,
                "comment": res.comment,
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat()
            })
            
        if current != None: result.append(current)
        return result

    def get(self, panel_id=None, version=None):
        """
            Generic method to get panels data according to provided filtering options
        """
        panel = Model.Panel.from_id(panel_id, 1)
        return  panel

        # if not isinstance(fields, dict):
        #     fields = None
        # if query is None:
        #     query = {}
        # if order is None:
        #     order = ["name"]
        # if offset is None:
        #     offset = 0
        # if limit is None:
        #     limit = RANGE_MAX
        # panels = Model.Session().query(Model.Panel).filter_by(**query).order_by(",".join(order)).limit(limit).offset(offset).all()
        # for p in panels: p.init(depth)
        # return panels




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
        if not isinstance(panel_data, dict): raise RegovarException(code="E202002")

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
        phenotype_res, disease_res = core.search.search_hpo(query)

        # Format result
        result = { 
            "total_result": len(gene_res) + len(phenotype_res) + len (disease_res),
            "gene":      gene_res,
            "phenotype": phenotype_res,
            "disease":   disease_res
        }
        return result

