#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *


# =====================================================================================================================
# EVENT
# =====================================================================================================================




Event = Base.classes.event
Event.public_fields = ["id", "analysis_id", "name", "filter", "description"]
