#!env/python3
# coding: utf-8
import ipdb
import json
import core.model as Model
from core.framework.common import *
from core.framework.erreurs_list import ERR





class EventManager:



    def list(self, user_id, fields=None, query=None, sort=None, offset=None, limit=None, depth=0):
        """
            Generic method to get events according to provided filtering options
        """
        # Check parameters
        fields, query, sort, offset, limit = check_generic_query_parameter(Model.User.public_fields, ['name'], fields, query, sort, offset, limit)

        # Build query
        result = []
        sql = "SELECT " + ','.join(fields) + " FROM \"user\""

        # Get result
        rsql = Model.execute(sql)

        # Get and return result
        for s in rsql:
            entry = {}
            for f in fields:
                if f == "roles" or f == "settings":
                    data = eval("s." + f)
                    if data:
                        entry.update({f: json.loads(eval("s." + f))})
                    else:
                        entry.update({f: None})
                else:
                    entry.update({f: eval("s." + f)})
            result.append(entry)
        return result


    def get(self, event_id, user_id):
        # TODO
        pass


    def edit(self, event_id, data, user_id):
        # TODO
        pass



    def delete(self, event_id, user_id):
        # TODO
        pass




