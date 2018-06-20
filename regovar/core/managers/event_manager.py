#!env/python3
# coding: utf-8
try:
    import ipdb
except ImportError:
    pass

import json
from core.framework.postgresql import *
from core.framework.common import *





class EventManager:



    def list(self, **kargs):
        """
            By default (without any argument) : Return last 100 "not technical" events logged"
        """
        # Build limit condition
        limit = max(0, min(RANGE_MAX, int(kargs["limit"]))) if "limit" in kargs else 100
        # Build where condition
        where = []
        if "event_id" in kargs:  where.append("id={0}".format(kargs["event_id"]))
        if "event_type" in kargs:  where.append("type='{0}'".format(kargs["event_type"]))
        else:  where.append("type<>'technical'")
        if "user_id" in kargs:  where.append("meta @> '{{\"user_id\": {} }}'".format(kargs["user_id"]))
        if "pipeline_id" in kargs:  where.append("meta @> '{{\"pipeline_id\": {} }}'".format(kargs["pipeline_id"]))
        if "job_id" in kargs:  where.append("meta @> '{{\"job_id\": {} }}'".format(kargs["job_id"]))
        if "project_id" in kargs:  where.append("meta @> '{{\"project_id\": {} }}'".format(kargs["project_id"]))
        if "analysis_id" in kargs:  where.append("meta @> '{{\"analysis_id\": {} }}'".format(kargs["analysis_id"]))
        if "subject_id" in kargs:  where.append("meta @> '{{\"subject_id\": {} }}'".format(kargs["subject_id"]))
        if "file_id" in kargs:  where.append("meta @> '{{\"file_id\": {} }}'".format(kargs["file_id"]))
        if "sample_id" in kargs:  where.append("meta @> '{{\"sample_id\": {} }}'".format(kargs["sample_id"]))
        if "filter_id" in kargs:  where.append("meta @> '{{\"filter_id\": {} }}'".format(kargs["filter_id"]))
        if "annotation_dbuid" in kargs:  where.append("meta @> '{{\"annotation_dbuid\": \"{}\"}}'".format(kargs["annotation_dbuid"]))
        if "variant_id" in kargs: 
            # TODO: a little bit more complicated :)
            # where.append("meta @> '{\"variant_id\": {0}}'".format(kargs["variant_id"]))
            pass
        if len(where) > 0:
            where = " WHERE " + ' AND '.join(where)
        else:
            where = ""
        
        sql = "SELECT id, author_id, date, message, type, meta FROM event{0} ORDER BY date DESC, id DESC LIMIT {1}".format(where, limit)
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "author_id": res.author_id,
                "date": res.date.isoformat(),
                "message": res.message,
                "type": res.type,
                "meta": res.meta
            })
        return result



    def get(self, event_id):
        """
            Get event by id
        """
        sql = "SELECT id, author_id, date, message, details, type, meta FROM event WHERE id={}".format(event_id)
        result = None
        for res in execute(sql): 
            result = {
                "id": res.id,
                "author_id": res.author_id,
                "date": res.date.isoformat(),
                "message": res.message,
                "details": res.details,
                "type": res.type,
                "meta": res.meta
            }
        return result
    
    
    
    def new(self, author_id, date, message, details=None, meta=None):
        """
            Create a new user custom event
        """
        # Check data
        date = check_date(date, datetime.datetime.now()).isoformat()
        message = sql_escape(message)
        details = "'" + sql_escape(details) + "'" if details else "NULL"
        metasql = self.check_meta_for_sql(meta)
        # Execute query
        sql = "INSERT INTO event (author_id, type, date, message, details, meta) VALUES ({0}, 'custom', '{1}', '{2}', {3}, {4}) RETURNING id;".format(author_id, date, message, details, metasql)
        event_id = execute(sql).first()[0]
        # Technical Log
        self.log(author_id, "technical", meta, "User (id={}) create new 'custom' event (id={})".format(author_id, event_id))
        # Return created event
        return self.get(event_id)



    def edit(self, author_id, event_id, date, message, meta, details=None):
        """
            Edit information of the event (user can only edit 'custom' events)
        """
        return None



    def delete(self, event_id, user_id):
        """
            Delete the event (user can only delete 'custom' events)
        """
        event = self.get(event_id)
        if event and event["type"] == "custom":
            sql = "DELETE FROM event WHERE id={}".format(event_id)
            execute(sql)
        else:
            log("Unable to delete the event (id={})".format(event_id))
            event = None
        return event
    
    
    
    def log(self, author_id, type, meta, message, details=None):
        """
            Create an event
        """
        # Check data
        author_id = author_id if author_id else "NULL"
        if type not in ["custom", "info", "warning", "error", "technical"]:
            type = "technical"
        if type == "warning": war(message)
        elif type == "error": err(message)
        elif type != "custom": log(message)
        meta = self.check_meta_for_sql(meta)
        message = sql_escape(message)
        details = "'" + sql_escape(details) + "'" if details else "NULL"
        # Execute query
        sql = "INSERT INTO event (author_id, type, meta, message, details) VALUES ({0}, '{1}', {2}, '{3}', {4}) RETURNING id;".format(author_id, type, meta, message, details)
        event_id = execute(sql).first()[0]
        return event_id
    
    def check_meta_json(self, meta):
        result = {}
        for k in meta.keys():
            if k.lower() in ["user_id", "pipeline_id", "job_id", "project_id", "analysis_id", "subject_id", "file_id", "sample_id", "filter_id"]:
                result[k.lower()] = int(meta[k])
            elif k.lower() in ["annotation_dbuid", "panel_id"]:
                result[k.lower()] = str(meta[k])
            elif k.lower() == "variant_id":
                # TODO: complex key for variant
                pass
        return result 

    def check_meta_for_sql(self, meta):
        if meta is not None:
            if meta is not isinstance(meta, str): 
                meta = self.check_meta_json(meta)
                meta = json.dumps(meta)
            meta = "'" + sql_escape(meta) + "'"
        else:
            meta = "NULL"
        return meta


