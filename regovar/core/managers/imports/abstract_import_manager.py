#!env/python3
# coding: utf-8







class AbstractImportManager():
    def __init__(self):
        # Description of the import script.
        # 
        self.metadata = {
            "name" : "VCF", # name of the import manager
            "input" :  ["vcf"],  # list of file extension that manage the import manager
            "description" : "Import variants from vcf file" # short desciption about what is imported
        }


    @staticmethod
    async def import_data(file_id, **kargs):
        raise NotImplementedError("The abstract method \"import_date\" of AbstractImportManager must be implemented.")
