#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *


# =====================================================================================================================
# Variant
# =====================================================================================================================


def variant_from_id(reference_id, variant_id):
    """
        Retrieve Sample with the provided id in the database
    """
    return __db_session.query(Variant).filter_by(id=variant_id).first()


Variant = Base.classes.variant_hg19
Variant.from_id = variant_from_id