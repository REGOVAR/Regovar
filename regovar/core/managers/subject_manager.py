#!env/python3
# coding: utf-8
import ipdb
import json
import core.model as Model
from core.framework.common import *
from core.framework.postgresql import execute





class SubjectManager:



    def list(self):
        """
            List all subjects with "minimal data"
        """
        sql = "SELECT id, identifier, firstname, lastname, sex, family_number, dateofbirth, comment, create_date, update_date FROM subject"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "identifier": res.identifier,
                "firstname": res.firstname,
                "lastname": res.lastname,
                "sex": res.sex,
                "family_number": res.family_number,
                "dateofbirth": res.dateofbirth.isoformat() if res.dateofbirth else None,
                "comment": res.comment,
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat()
            })
        return result




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
        s = Model.Session()
        subjects = s.query(Model.Subject).filter_by(**query).order_by(",".join(order)).limit(limit).offset(offset).all()
        for s in subjects: s.init(depth, True)
        return subjects




    def delete(self, subject_id):
        """ 
            Delete the subject
        """
        subject = Model.Subject.from_id(subject_id)
        if not subject: raise RegovarException(code="E102001", args=[subject_id])
        # TODO
        # regovar.log_event("Delete user {} {} ({})".format(user.firstname, user.lastname, user.login), user_id=0, type="info")





    def create_or_update(self, subject_data, loading_depth=1):
        """
            Create or update a subject with provided data.
        """
        if not isinstance(subject_data, dict): raise RegovarException(code="E202002")

        sid = None
        if "id" in subject_data.keys():
            sid = subject_data["id"]

        # Get or create the subject
        subject = Model.Subject.from_id(sid, loading_depth) or Model.Subject.new()
        subject.load(subject_data)
        return subject




