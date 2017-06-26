#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *


# =====================================================================================================================
# INDICATOR
# =====================================================================================================================



Indicator = Base.classes.indicator
Indicator.public_fields = ["id", "name", "description", "default_value_id"]





IndicatorValue = Base.classes.indicator_value
Indicator.public_fields = ["id", "indicator_id", "name", "description", "style"]



