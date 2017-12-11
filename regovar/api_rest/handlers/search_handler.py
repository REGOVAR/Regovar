#!env/python3
# coding: utf-8
import ipdb; 




from core.framework.common import *
from core.model import *
from core.core import core
from api_rest.rest import *





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# SEARCH HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class SearchHandler:


    def search(self, request):
        """ 
            Search provided query
        """
        searchQuery = request.match_info.get('query', None)
        if searchQuery is None :
            return rest_error("Nothing to search...")
        
        try:
            result = core.search.search(searchQuery)
        except RegovarException as ex:
            return rest_error("Error occured while trying to search", e)
        
        return rest_success(result)




    def fetch_variant(self, request):
        """
            Return all data available for the requested variant in the context of the analysis
        """
        reference_id = request.match_info.get('ref_id', -1)
        variant_id = request.match_info.get('variant_id', -1)
        analysis_id = request.match_info.get('analysis_id', None)

        variant = core.search.fetch_variant(reference_id, variant_id, analysis_id)
        if variant is None:
            return rest_error('Variant not found')
        return rest_success(variant)



    def fetch_gene(self, request):
        genename = request.match_info.get('gene_name', None)
        if genename is None :
            return rest_error("Nothing to fetch...")
        
        try:
            result = core.search.fetch_gene(genename)
        except RegovarException as ex:
            return rest_error("Error occured while trying to fetch information of the gene + " + genename, ex)
        
        return rest_success(result)



    def fetch_hpo(self, request):
        return rest_error("Not yet implemented")





    




    




 
