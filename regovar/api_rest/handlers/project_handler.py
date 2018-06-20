 
#!env/python3
# coding: utf-8
try:
    import ipdb
except ImportError:
    pass



import os
import json
import aiohttp
import datetime
import time


from config import *
from core.framework.common import *
from core.framework.tus import *
from core.model import *
from api_rest.rest import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# PROJECT HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 





class ProjectHandler:


    # def build_tree(parent_id):
    #     """
    #         Recursive method to build treeview of folders/projects
    #     """
    #     from core.core import core
    #     currentLevelProjects = core.projects.get(None, {"parent_id": parent_id, "is_sandbox": False}, None, None, None, 1)
    #     result = []
    #     for p in currentLevelProjects:
    #         entry = p.to_json(["id", "name", "comment", "parent_id", "update_date", "create_date", "is_sandbox", "is_folder"])

    #         if p.is_folder:
    #             entry["children"] = ProjectHandler.build_tree(p.id)
    #         else:
    #             analyses = p.analyses
    #             for a in analyses: a.update({"type": "analysis"})
    #             jobs = p.jobs
    #             for j in jobs: j.update({"type":"pipeline"})
    #             entry["subjects"] = p.subjects
    #             entry["analyses"] = analyses + jobs
    #         result.append(entry)
    #     return result



    # def tree(self, request):
    #     """
    #         Get projects as tree
    #     """
    #     return rest_success(ProjectHandler.build_tree(None))


    @user_role('Authenticated')
    def list(self, request):
        """
            Get list of all projects
        """
        return rest_success(core.projects.list())
        
    
    @user_role('Authenticated')
    async def create_or_update(self, request):
        """
            Create or update a project with provided data
        """
        from core.core import core
        project_id = request.match_info.get('project_id', -1)
        data = await request.json()

        if isinstance(data, str) : data = json.loads(data)
        # If provided by the query parameter, ensure that we use the query project_id
        if project_id != -1:
        	data["id"] = project_id
        # Create or update the project
        try:
            project = core.projects.create_or_update(data)
        except RegovarException as ex:
            return rest_exception(ex)
        if project is None:
            return rest_error("Unable to create a new project.")
        return rest_success(project.to_json())
        
        
    @user_role('Authenticated')
    def get(self, request):
        """
            Get details about the project
        """
        project_id = request.match_info.get('project_id', -1)
        project = Project.from_id(project_id, 1)
        if not project:
            return rest_error("Unable to find the project (id={})".format(project_id))
        return rest_success(project.to_json())
        
    
    
    
    @user_role('Authenticated')
    def delete(self, request):
        """
            Delete the project
        """
        from core.core import core
        project_id = request.match_info.get('project_id', -1)
        try:
            project = core.projects.delete(project_id)
        except Exception as ex:
            return rest_error("Unable to delete the project (id={})".format(project_id), exception=ex)
        return rest_success(project)
    
    
    
    @user_role('Authenticated')
    def events(self, request):
        """
            Get list of events of the project (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Project.public_fields)
        project_id = request.match_info.get('project_id', -1)
        user_id = None # TODO: retrieve user id from session
        depth = 0
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Project.count(),
            "range_max"    : RANGE_MAX,
        }
        events = core.events.list(user_id, fields, query, order, offset, limit, depth)
        return rest_success([e.to_json() for e in events], range_data)


    @user_role('Authenticated')
    def subjects(self, request):
        """
            Get list of subjects of the project (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Project.public_fields)
        project_id = request.match_info.get('project_id', -1)
        depth = 0
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Project.count(),
            "range_max"    : RANGE_MAX,
        }
        subjects = core.subjects.get(fields, query, order, offset, limit, depth)
        return rest_success([s.to_json() for s in subjects], range_data)
    
    
    @user_role('Authenticated')
    def analyses(self, request):
        """
             Get list of tasks (jobs and analyses) of the project (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Project.public_fields)
        depth = 0
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Project.count(),
            "range_max"    : RANGE_MAX,
        }
        jobs = core.jobs.get(fields, query, order, offset, limit, depth)
        analyses = core.analyses.get(fields, query, order, offset, limit, depth)
        tasks = array_merge(jobs, analyses)
        return rest_success([t.to_json() for t in tasks], range_data)


    @user_role('Authenticated')
    def files(self, request):
        """
            Get list of subjects of the project (allow search parameters)
        """
        from core.core import core
        fields, query, order, offset, limit = process_generic_get(request.query_string, Project.public_fields)
        project_id = request.match_info.get('project_id', -1)
        depth = 0
        # Get range meta data
        range_data = {
            "range_offset" : offset,
            "range_limit"  : limit,
            "range_total"  : Project.count(),
            "range_max"    : RANGE_MAX,
        }
        files = core.files.get(fields, query, order, offset, limit, depth)
        return rest_success([f.to_json() for f in files], range_data)
    
    











