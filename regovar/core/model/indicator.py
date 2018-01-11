#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *


# =====================================================================================================================
# INDICATOR
# =====================================================================================================================



Indicator = Base.classes.indicator
Indicator.public_fields = ["id", "name", "description", "meta"]





def indicator_from_analysis_id(analysis_id):
    return []

def indicator_from_job_id(job_id):
    return []

def indicator_from_subject_id(subject_id):
    return []

Indicator.from_analysis_id = indicator_from_analysis_id
Indicator.from_job_id = indicator_from_job_id
Indicator.from_subject_id = indicator_from_subject_id