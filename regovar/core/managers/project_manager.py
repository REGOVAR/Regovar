#!env/python3
# coding: utf-8
import ipdb
import json
import core.model as Model
from core.framework.common import *
from core.framework.erreurs_list import ERR

from config import *



class ProjectManager:

    def __init__(self):
        pass


    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
        """
            Generic method to get projects data according to provided filtering options
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {}
        if order is None:
            order = "name"
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        s = Model.session()
        projects = s.query(Model.Project).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for p in projects: p.init(depth)
        return projects




    def delete(self, project_id):
        """ 
            Delete the project
        """
        project = Model.Project.from_id(project_id)
        if not project: raise RegovarException(ERR.E102001.format(project_id), "E102001")
        # TODO
        # regovar.log_event("Delete user {} {} ({})".format(user.firstname, user.lastname, user.login), user_id=0, type="info")





    def create_or_update(self, project_data, loading_depth=1):
        """
            Create or update a project with provided data.
        """
        if not isinstance(project_data, dict): raise RegovarException(ERR.E202002, "E202002")

        pid = None
        if "id" in project_data.keys():
            pid = project_data["id"]

        # Get or create the project
        project = Model.Project.from_id(pid, loading_depth) or Model.Project.new()
        project.load(project_data)
        return project
    
    
    
    