#!env/python3
# coding: utf-8


from config import *
from core.framework.common import *
from core.framework.tus import *
from core.model import *
from core.core import core
from api_rest.rest import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# ANALYSIS HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class VariantHandler:

    @staticmethod
    def get(request):
        """
            Return all data available for the requested variant in the context of the analysis
        """
        reference_id = request.match_info.get('ref_id', -1)
        variant_id = request.match_info.get('variant_id', -1)
        analysis_id = request.match_info.get('analysis_id', None)

        variant = core.variants.get(reference_id, variant_id, analysis_id)
        if variant is None:
            return rest_error('Variant not found')
        return rest_success(variant)


    @staticmethod
    async def new(request):
        """
            Create new variant with provided json data (POST)
        """
        data = await request.json()
        try:
            if "variants" in data.keys():
                count = 0
                for var in data["variants"]:
                    core.variants.new(var)
                    count += 1
        except Exception as ex:
            return rest_error("Unable to import variants. {}".format(ex))

        return rest_success(count)
 
