#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *


# =====================================================================================================================
# EVENT
# =====================================================================================================================






def event_from_id(event_id):
    """
        Retrieve Event with the provided id in the database
    """
    event = Session().query(Event).filter_by(id=event_id).first()
    Session().refresh(event)
    return event




Event = Base.classes.event
Event.public_fields = ["id", "date", "message", "type", "meta"]
Event.from_id = event_from_id