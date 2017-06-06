#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *





# =====================================================================================================================
# SAMPLE
# =====================================================================================================================


def sample_from_id(sample_id):
    """
        Retrieve Sample with the provided id in the database
    """
    return session().query(Sample).filter_by(id=sample_id).first()


def sample_to_json(self, fields=None):
    """
        export the sample into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Sample.public_fields
    for f in fields:
        result.update({f: eval("self." + f)})
    return result


Sample = Base.classes.sample
Sample.public_fields = ["id", "name", "comments", "is_mosaic"]
Sample.from_id = sample_from_id
Sample.to_json = sample_to_json



# =====================================================================================================================
# SAMPLE FILE
# =====================================================================================================================
SampleFile = Base.classes.sample_file




# =====================================================================================================================
# SAMPLE VARIANT
# =====================================================================================================================

SampleVariant = Base.classes.sample_variant_hg19