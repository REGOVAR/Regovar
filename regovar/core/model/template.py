#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *



# =====================================================================================================================
# TEMPLATE
# =====================================================================================================================


def template_from_id(template_id):
    """
        Retrieve Template with the provided id in the database
    """
    return __db_session.query(Template).filter_by(id=template_id).first()


Template = Base.classes.template
Template.public_fields = ["id", "name", "author", "description", "version", "creation_date", "update_date"]
Template.from_id = template_from_id