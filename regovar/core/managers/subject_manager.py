#!env/python3
# coding: utf-8
import ipdb
import json
import core.model as Model
from core.framework.common import *
from core.framework.erreurs_list import ERR





class SubjectManager:



    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
        """
            Generic method to get subject data according to provided filtering options
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {}
        if order is None:
            order = ["lastname", "firstname"]
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        s = Model.session()
        subjects = s.query(Model.Subject).filter_by(**query).order_by(",".join(order)).limit(limit).offset(offset).all()
        for s in subjects: s.init(depth)
        return subjects




    def delete(self, subject_id):
        """ 
            Delete the subject
        """
        subject = Model.Subject.from_id(subject_id)
        if not subject: raise RegovarException(ERR.E102001.format(subject_id), "E102001")
        # TODO
        # regovar.log_event("Delete user {} {} ({})".format(user.firstname, user.lastname, user.login), user_id=0, type="info")





    def create_or_update(self, subject_data, loading_depth=1):
        """
            Create or update a subject with provided data.
        """
        if not isinstance(subject_data, dict): raise RegovarException(ERR.E202002, "E202002")

        sid = None
        if "id" in subject_data.keys():
            sid = subject_data["id"]

        # Get or create the subject
        subject = Model.Subject.from_id(sid, loading_depth) or Model.Subject.new()
        subject.load(subject_data)
        return subject




