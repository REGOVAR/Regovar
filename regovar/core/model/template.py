#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *



# =====================================================================================================================
# TEMPLATE
# =====================================================================================================================

def template_init(self, loading_depth=0):
    """
        If loading_depth is > 0, children objects will be loaded. Max depth level is 2.
        Children objects of a template are :
            
        If loading_depth == 0, children objects are not loaded
    """
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    # TODO
    self.load_depth(loading_depth)
            

def template_load_depth(self, loading_depth):
    pass
    # TODO




def template_from_id(template_id, loading_depth=0):
    """
        Retrieve Template with the provided id in the database
    """
    template = session().query(Template).filter_by(id=template_id).first()
    if template:
        template.init(loading_depth)
    return template


Template = Base.classes.template
Template.public_fields = ["id", "name", "author", "description", "version", "create_date", "update_date"]
Template.init = template_init
Template.load_depth = template_load_depth
Template.from_id = template_from_id
