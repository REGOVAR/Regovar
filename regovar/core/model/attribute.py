#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *



class AttributeWrapper:
    def __init__(self, name):
        self.name = name
        self.samples_values = {}
        self.values = []
        
    def add_value(self, sample_id, value):
        if value not in self.values:
            self.values.append(value)
        self.samples_values[sample_id] = value

            



def attribute_get_attribute(analysis_id,  loading_depth=0):
    result = []
    attributes = session().query(Attribute).filter_by(analysis_id=analysis_id).order_by("name, sample_id").all()
    AttributeWrapper = None
    for a in attributes:
        if current_attribute is None or AttributeWrapper.name != a.name:
            current_attribute = AttributeWrapper(name)
            result.append(current_attribute)
        current_attribute.add_value(a.sample_id, a.value)
    return result




def attribute_delete(analysis_id):
    """
        Delete the Analysis with the provided id in the database
    """
    # TODO : delete linked filters, AnalysisSample, Attribute, WorkingTable
    session().query(Analysis).filter_by(id=analysis_id).delete(synchronize_session=False)


def attribute_new(analysis_id, sample_id, name, value=None):
    """
        Create a new Analysis and init/synchronise it with the database
    """
    
    a = Attribute(analysis_id=analysis_id, sample_id=sample_id, name=name, value=value)
    a.save()
    a.init()
    return a





        
Attribute = Base.classes.attribute
Attribute.public_fields = ["sample_id", "analysis_id", "name", "value"]
Attribute.get_attributes = attribute_get_attribute
Attribute.save = generic_save
Attribute.delete = attribute_delete
Attribute.new = attribute_new

