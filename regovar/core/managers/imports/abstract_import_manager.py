#!env/python3
# coding: utf-8
import ipdb

from core.framework.common import log, war, err




class AbstractImportManager():
    def __init__(self):
        # Description of the import script.
        metadata = {
            "name" : "VCF", # name of the import manager
            "input" :  ["vcf"],  # list of file extension that manage the import manager
            "description" : "Import variants from vcf file" # short desciption about what is imported
        }

    @staticmethod
    async def import_data(file_id, **kargs):
        raise NotImplementedError("The abstract method \"import_date\" of AbstractImportManager must be implemented.")







class AbstractTranscriptDataImporter():
    
    def __init__(self):
        self.reference_id = -1        # Id of the reference
        self.name = ""                # Name of the annotation db
        self.version = ""             # Version of the annotation db
        self.description = ""         # Description of the annotation db
        
        self.table_name = ""          # Name of the table : regovar name must have following pattern "{name}_{version}_{reference_id}" 
                                    #   and must be sanytise with normalise_annotation_name method
        self.columns = []             # List of column's names to import from the VCF
        self.vcf_flag = ""            # Flag use in the VCF to retrieve data in the INFOS field
        self.colums_as_pk = 'feature' # The column name that will be use as primary key for transcript id.
                                    #   if this column is not present in the VCF, the import cannot be done
        self.db_uid = ""              # UID of the annotation db in Regovar database
        self.columns_mapping = {}     # Mapping information for vcf columns into Regovar database
        
        # This attribute shall contains the definition of all supported data comming from the VCF
        # Structure MUST BE :
        # columns_definitions = {
        #   "sanitised column name in the vcf" : {
        #       "type"        : "int|string|float|enum|range|bool|sequence|list|sample_array",
        #       "description" : "the description of the field for the end_user"
        #   }}
        self.columns_definitions = {}
    
    # ===========================================================================================================
    # TOOLS 
    # ===========================================================================================================
    

    
    
    
    def normalise_annotation_name(self, name):
        """
            Tool to convert a name of a annotation tool/db/field/version into the corresponding valid name for the database
        """
        if name[0].isdigit():
            name = '_'+name
        def check_char(char):
            if char in ['.', '-', '_', '/']:
                return '_'
            elif char.isalnum():
                # TODO : remove accents
                return char.lower()
            else:
                return ''
        return ''.join(check_char(c) for c in name)



    def escape_value_for_sql(self, value):
        if type(value) is str:
            value = value.replace('%', '%%')
            value = value.replace("'", "''")

            # Workaround for some annotations that can crash the script
            value = value.replace('-:0', '-: 0')   # VEP aa_maf = "-:0.1254..." for weird raison: -:0 is interpreted as {0} by format method
        return value
    
    
    def value_to_regovar_type(self, value, regovar_type):
        if value is None or value.strip() in ['', '-']: return True, None
         
        success = True
        result = value
        try:
            if regovar_type == "int":
                result = int(value)
            elif regovar_type == "float":
                result = float(value)
            elif regovar_type == "bool":
                result = bool(value)
            elif regovar_type == "list":
                result = "ARRAY [{}]".format(",".join(["'{}'".format(self.escape_value_for_sql(v)) for v in value.split('&')]))
            else:
                result = "'{}'".format(self.escape_value_for_sql(value))
        except Exception as ex:
            ipdb.set_trace()
            war("VEP import : enable to import {} cast into {}".format(value, regovar_type))
            success = False
            result = None
            
        return success, result
    
    
    # ===========================================================================================================
    # SPECIFIC METHODS / ATTRIBUTES
    # ===========================================================================================================
    def init(self, headers, reference_id):
        """
            Check VCF headers and return true if VEP data can be imported; false otherwise
            By the way, when VEP data are here, init internal data of the importer
        """
        raise NotImplementedError("The abstract method \"init\" of AbstractTranscriptDataImporter must be implemented.")
    
    
    def check_annotation_table(self):
        """
            Check if annotation table exists and create it according to information collected by the init method
        """
        raise NotImplementedError("The abstract method \"check_annotation_table\" of AbstractTranscriptDataImporter must be implemented.")
        
        
    def import_annotations(self, sql_pattern, bin, chrm, pos, ref, alt, infos):
        """
            Return the query according to the provided pattern filled with annotation informations
            Also return the count of new entry inserted by the query 
        """
        raise NotImplementedError("The abstract method \"import_annotations\" of AbstractTranscriptDataImporter must be implemented.")
    
        
        
        
        