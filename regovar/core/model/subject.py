#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *


# =====================================================================================================================
# SUBJECT
# =====================================================================================================================



Subject = Base.classes.subject
Subject.public_fields = ["id", "analysis_id", "name", "filter", "description"]