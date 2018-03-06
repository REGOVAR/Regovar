#!env/python3
# coding: utf-8
import ipdb
import json
from core.framework.postgresql import *
from core.framework.common import *





class EventManager:



    def list(self, **kargs):
        """
            By default (without any argument) : Return last 100 events logged"
        """
        # Build limit condition
        limit = max(0, min(RANGE_MAX, int(kargs["limit"]))) if "limit" in kargs else 100
        # Build where condition
        where = []
        if "event_id" in kargs:  where.append("id={0}".format(kargs["event_id"]))
        if "event_type" in kargs:  where.append("type='{0}'".format(kargs["event_type"]))
        if "user_id" in kargs:  where.append("meta @> '{\"user_id\": {0}}'".format(kargs["user_id"]))
        if "pipeline_id" in kargs:  where.append("meta @> '{\"pipeline_id\": {0}}'".format(kargs["pipeline_id"]))
        if "job_id" in kargs:  where.append("meta @> '{\"job_id\": {0}}'".format(kargs["job_id"]))
        if "project_id" in kargs:  where.append("meta @> '{\"project_id\": {0}}'".format(kargs["project_id"]))
        if "analysis_id" in kargs:  where.append("meta @> '{\"analysis_id\": {0}}'".format(kargs["analysis_id"]))
        if "subject_id" in kargs:  where.append("meta @> '{\"subject_id\": {0}}'".format(kargs["subject_id"]))
        if "file_id" in kargs:  where.append("meta @> '{\"file_id\": {0}}'".format(kargs["file_id"]))
        if "sample_id" in kargs:  where.append("meta @> '{\"sample_id\": {0}}'".format(kargs["sample_id"]))
        if "filter_id" in kargs:  where.append("meta @> '{\"filter_id\": {0}}'".format(kargs["filter_id"]))
        if "annotation_dbuid" in kargs:  where.append("meta @> '{\"annotation_dbuid\": \"{0}\"}'".format(kargs["annotation_dbuid"]))
        if "variant_id" in kargs: 
            # TODO: a little bit more complicated :)
            # where.append("meta @> '{\"variant_id\": {0}}'".format(kargs["variant_id"]))
            pass
        if len(where) > 0:
            where = " WHERE " + ' AND '.join(where)
        else:
            where = ""
        
        sql = "SELECT id, date, message, type, meta FROM event{0} ORDER BY date DESC, id DESC LIMIT {1}".format(where, limit)
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
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
        result = self.list(event_id=event_id)
        return None if len(result) == 0 else result[0]


    def edit(self, event_id, data, from_user_id):
        """
            Edit information of the event
        """
        return None



    def delete(self, event_id, user_id):
        """
            Delete the event (user can only delete 'custom' events
        """
        event = self.get(event_id)
        if event and event["type"] == "custom":
            sql = "DELETE FROM event WHERE id={}".format(event_id)
            execute(sql)
        else:
            log("Unable to delete the event (id={})".format(event_id))
            event = None
        return event
    
    
    def new(self, user_id, date, message, meta):
        """
            Create a new user custom event
        """
        return None
    
    
    def log(self, message, type):
        """
            Create an auto "system" event
        """
        return None
    




