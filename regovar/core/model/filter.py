#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *


# =====================================================================================================================
# FILTER
# =====================================================================================================================


def filter_from_id(filter_id):
    """
        Retrieve Filter with the provided id in the database
    """
    return __db_session.query(Filter).filter_by(id=filter_id).first()


def filter_to_json(self, fields=None):
    """
        export the filter into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Filter.public_fields
    for f in fields:
        result.update({f: eval("self." + f)})
    return result


Filter = Base.classes.filter
Filter.public_fields = ["id", "analysis_id", "name", "filter", "description"]
Filter.from_id = filter_from_id
Filter.to_json = filter_to_json