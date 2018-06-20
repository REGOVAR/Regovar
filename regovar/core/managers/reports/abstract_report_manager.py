#!env/python3
# coding: utf-8
try:
    import ipdb
except ImportError:
    pass


from core.framework.common import log, war, err




class AbstractReportManager():
    def __init__(self):
        # Description of the export script.
        metadata = {
            "name" : "<AbstractReport>", # name of the report manager
            "output" :  "html",  # the type of the report created (can be one of standart file extension like pdf, txt, vcf, ..., or a website (index.hml + several assets files)
            "description" : "Description of the report" # short desciption about what it does
        }

    @staticmethod
    async def generate(analysis_id, parameters):
        raise NotImplementedError("The abstract method \"generate\" of AbstractReport must be implemented.")






        
         
