#!env/python3
# coding: utf-8
import ipdb
import json
import core.model as Model
from core.framework.common import *
from core.framework.postgresql import execute
from config import *



class ProjectManager:


    def list(self):
        """
            List all projects with "minimal data"
        """
        sql = "SELECT p.id, p.name, p.comment, p.parent_id, p.is_folder, p.create_date, p.update_date, array_agg(DISTINCT a.id) as analyses, array_agg(DISTINCT j.id) as jobs FROM project p LEFT JOIN analysis a ON a.project_id=p.id LEFT JOIN job j ON j.project_id=p.id where not is_sandbox GROUP BY p.id, p.name, p.comment, p.parent_id, p.is_folder, p.create_date, p.update_date ORDER BY p.parent_id, p.name"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "name": res.name,
                "comment": res.comment,
                "parent_id": res.parent_id,
                "is_folder": res.is_folder,
                "analyses": res.analyses if res.analyses[0] else [],
                "jobs": res.jobs if res.jobs[0] else [],
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat()
            })
        return result

    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
        """
            Generic method to get projects data according to provided filtering options
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {"id>0"}
        if order is None:
            order = "name"
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        projects = Model.Session().query(Model.Project).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for p in projects: p.init(depth)
        return projects




    def delete(self, project_id):
        """ 
            Delete the project
            All its analyses are put into the trash project (id = 0)
        """
        project = Model.Project.from_id(project_id)
        if not project: raise RegovarException(code="E102001", arg=[project_id])
        sql = "UPDATE analysis SET project_id=0 WHERE project_id={0}; DELETE FROM project WHERE id={0}".format(project.id)
        result = project.to_json()
        Model.execute(sql)
        return result





    def create_or_update(self, project_data, loading_depth=1):
        """
            Create or update a project with provided data.
        """
        if not isinstance(project_data, dict): raise RegovarException(code="E202002")

        pid = None
        if "id" in project_data.keys():
            pid = project_data["id"]

        # Get or create the project
        project = Model.Project.from_id(pid, loading_depth) or Model.Project.new()
        project.load(project_data)
        return project
    
    
    
    