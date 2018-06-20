#!env/python3
# coding: utf-8

try:
    import ipdb
except ImportError:
    pass

import sqlalchemy

from core.managers.imports.abstract_import_manager import AbstractTranscriptDataImporter
from core.framework.common import *
import core.model as Model


class SnpEffImporter(AbstractTranscriptDataImporter): 
    
    
    # ===========================================================================================================
    # SnpEff IMPORT METHODS 
    # ===========================================================================================================
        
    def init(self, headers, reference_id):
        """
            Check VCF headers and return true if SnpEff data can be imported; false otherwise
            By the way, when SnpEff data are here, init internal data of the importer
        """
        result = False
        
        if 'SnpEffVersion' in headers.keys() :
            vcf_flag = None
            if 'EFF' in headers['INFO'].keys():
                vcf_flag = 'EFF'
                err("TODO: Old SnpEff annotation (EFF) importation is not implemented")
                
            elif 'ANN' in headers['INFO'].keys():
                vcf_flag = 'ANN'
                reference_name = Model.execute("SELECT table_suffix FROM reference WHERE id={}".format(reference_id)).first()[0]
                data = headers['INFO'][vcf_flag]['description'].split('Functional annotations:')
                self.name = "SnpEff"
                self.reference_id = reference_id
                self.description = "SnpEff variant annotation and effect prediction tool."
                self.columns = [self.normalise_annotation_name(c).title() for c in data[1].strip().strip("'").split('|')]
                self.version = headers['SnpEffVersion'][0].strip().strip('"').split(' ')[0]
                self.table_name = self.normalise_annotation_name('{}_{}_{}'.format('SnpEff', self.version, reference_name))
                self.vcf_flag = vcf_flag
                self.columns_definitions = SnpEffImporter.columns_definitions
                result = 'Feature_Id' in self.columns
                
                
                
        if result:
            self.check_annotation_table()

        print("SnpEff init : ", result)
        return result
    
    
    
    def check_annotation_table(self):
        """
            Check if annotation table exists and create it according to information collected by the init method
        """
        # check if vep_version table exists
        
        columns_mapping = {}
        db_uid = Model.execute("SELECT uid FROM annotation_database WHERE name='{}'".format(self.table_name)).first()
        
        if db_uid is not None:
            db_uid = db_uid[0]
        else:
            # Create new table
            pattern = "CREATE TABLE {0} (variant_id bigint, bin integer, chr integer, pos bigint, ref text, alt text, regovar_trx_id character varying(100), {1}, CONSTRAINT {0}_ukey UNIQUE (variant_id, regovar_trx_id));"
            query   = ""
            db_map = {}
            fields = []
            type_map = {"string" : "text", "int" : "integer", "float" : "real", "bool" : "boolean", "enum" : "varchar(50)", "list" : "varchar(250)[]"}
            for col_name in self.columns_definitions.keys():
                fields.append("{} {}".format(col_name, type_map[self.columns_definitions[col_name]["type"]])) 
            query += pattern.format(self.table_name, ', '.join(fields))
            query += "CREATE INDEX {0}_idx_vid ON {0} USING btree (variant_id);".format(self.table_name)
            query += "CREATE INDEX {0}_idx_var ON {0} USING btree (bin, chr, pos);".format(self.table_name)
            
            # Register annotation DB
            db_uid, pk_uid = Model.execute("SELECT MD5('{0}'), MD5(concat(MD5('{0}'), '{1}'))".format(self.table_name, self.colums_as_pk)).first()
            query += "CREATE INDEX {0}_idx_tid ON {0} USING btree (regovar_trx_id);".format(self.table_name)
            query += "INSERT INTO annotation_database (uid, reference_id, name, version, name_ui, description, ord, type, db_pk_field_uid, jointure) VALUES "
            q = "('{0}', {1}, '{2}', '{3}', '{4}', '{5}', {6}, '{7}', '{8}', '{2} {{0}} ON {{0}}.bin={{1}}.bin AND {{0}}.chr={{1}}.chr AND {{0}}.pos={{1}}.pos AND {{0}}.ref={{1}}.ref AND {{0}}.alt={{1}}.alt');"
            query += q.format(
                db_uid, 
                self.reference_id, 
                self.table_name, 
                self.version, 
                self.name, 
                self.description, 
                30, 
                'transcript',
                pk_uid)
            query += "INSERT INTO annotation_field (database_uid, ord, name, name_ui, type, description) VALUES "
            
            # Register annotation Fields
            fields = [field for field in self.columns_definitions.keys()]
            fields.sort()
            for idx, col_name in enumerate(fields):
                query += "('{0}', {1}, '{2}', '{3}', '{4}', '{5}'),".format(db_uid, idx, col_name, col_name.title(), self.columns_definitions[col_name]["type"], self.escape_value_for_sql(self.columns_definitions[col_name]["description"]))
            
            Model.execute(query[:-1])
            Model.execute("UPDATE annotation_field SET uid=MD5(concat(database_uid, name)) WHERE uid IS NULL;")
        


        # Retrieve column mapping for column in vcf
        self.columns = [self.normalise_annotation_name(s) for s in self.columns]

        for col in Model.execute("SELECT name, name_ui, type FROM annotation_field WHERE database_uid='{}'".format(db_uid)):
            if col.name in self.columns:
                columns_mapping[col.name] = {'name': col.name, 'type': col.type, 'name_ui': col.name_ui}
        for col in self.columns:
            if col not in columns_mapping.keys():
                columns_mapping[col] = False

        self.db_uid = db_uid
        self.columns_mapping = columns_mapping
        return db_uid, columns_mapping
    
    

    def import_annotations(self, sql_pattern, bin, chrm, pos, ref, alt, infos):
        # split annotations according to columns order retrieve in the init method : see self.columns
        # create sql query with corresponding field uid
        # manage special case for sift and polyphen that are split in 2 fields : _pred and _score
        # manage type conversion when needed !
        count = 0
        query = ""
        def check_val(val):
            result = 'NULL'
            if val is not None:
                if isinstance(val, str) and val != '':
                    result = '\'{}\''.format(val)
                result = val
            return result
    
        
        for info in infos[self.vcf_flag]:
            data = info.split('|')
            q_fields = []
            q_values = []
            allele   = ""
            trx_pk = "NULL"
            
            for col_pos, col_name in enumerate(self.columns):
                try:
                    vals = [self.escape_value_for_sql(data[col_pos])]
                    
                    col_mapping = self.columns_mapping[col_name]
                    fields = [col_name]

                    if not col_mapping:
                        # war("Unable to import vcf SnpEff annotation : {} ({}). No column mapping/definition provided. SKIPPED".format(col_name, ','.join(vals)))
                        continue
                    
                    # Manage specials annotations
                    if col_name == 'allele':
                        allele = vals[0].strip().strip('-') # When deletion, SnpEff use '-', but regovar just let empty string.
                        success, new_value = self.value_to_regovar_type(vals[0], "string")
                        vals = [new_value]
                    elif col_name == 'feature_id':
                        trx_pk = vals[0].strip()
                        success, new_value = self.value_to_regovar_type(vals[0], "string")
                        vals = [new_value]
                    elif col_name == 'annotation_impact':
                        new_value = vals[0]
                        if new_value:
                            if new_value[0] == "{": new_value = new_value[1:]
                            if new_value[-1] == "}": new_value = new_value[:-1]  
                            success, new_value = self.value_to_regovar_type(new_value.lower(), "string")
                            vals = [new_value]                          
                    elif col_name in ['annotation', 'annotation_impact']:
                        vals = ["ARRAY [{}]".format(",".join(["'{}'".format(self.escape_value_for_sql(v)) for v in data[col_pos].split('&')]))]
                   
                   
                    elif col_name not in self.columns_mapping:
                        # if annotation field not supported, continue with next
                        # this test is done at last to manage case like sift and polyphen that are not directly supported
                        continue
                    else:
                        # for other fields, try to convert it into the requiered type else escape
                        success, new_value = self.value_to_regovar_type(vals[0], col_mapping["type"])
                        if success:
                            vals = [new_value]
                        else:
                            continue
                        
                    q_fields += fields
                    q_values += [check_val(val) for val in vals]
                except Exception as ex:
                    err("import_annotations error when trying to import {}='{}'".format(col_name, vals),ex)
            

            if len(q_fields) > 0:
                query += sql_pattern.format(self.table_name, ','.join(q_fields), ','.join([str(val) for val in q_values]), bin, chrm, pos, ref, allele, trx_pk)
                count += 1
                
        return query, count

    
    
    
    
    
    
    
    
    
    
    
    
    
 
    
    
    
    
    # When need to create annotation table/field : to create columns with good type and description
    columns_definitions = {
        "allele" :               { "type" : "string", "description" : "The variant allele used to calculate the consequence"},
        "annotation" :           { "type" : "list",   "description" : "Annotated using Sequence Ontology terms (a.k.a. effect)"},
        "annotation_impact" :    { "type" : "enum",   "description" : "A simple estimation of putative impact / deleteriousness : {HIGH, MODERATE, LOW, MODIFIER}"},
        "gene_name" :            { "type" : "string", "description" : "Common gene name (HGNC). Optional: use closest gene when the variant is \"intergenic\""},
        "gene_id" :              { "type" : "string", "description" : "Gene ID"},
        "feature_type" :         { "type" : "string", "description" : "Which type of feature is in the \"Feature Type\" field (e.g. transcript, motif, miRNA, etc.). It is preferred to use Sequence Ontology (SO) terms, but \"custom\" (user defined) are allowed"},
        "feature_id" :           { "type" : "string", "description" : "Depending on the annotation, this may be: Transcript ID (preferably using version number), Motif ID, miRNA, ChipSeq peak, Histone mark, etc. Note: Some features may not have ID (e.g. histone marks from custom Chip-Seq experiments may not have a unique ID)"},
        "transcript_bioType" :   { "type" : "string", "description" : "The bare minimum is at least a description on whether the transcript is {\"Coding\", \"Noncoding\"}. Whenever possible, use ENSEMBL biotypes"},
        "rank" :                 { "type" : "string", "description" : "Exon or Intron rank / total number of exons or introns"},
        "hgvs_c" :               { "type" : "string", "description" : "Variant using HGVS notation (DNA level)"},
        "hgvs_p" :               { "type" : "string", "description" : "If variant is coding, this field describes the variant using HGVS notation (Protein level). Since transcript ID is already mentioned in ‘feature ID’, it may be omitted here"},
        "cdna_pos_cdna_length" : { "type" : "string", "description" : "Position in cDNA and trancript’s cDNA length (one based)"},
        "cds_pos_cds_length" :   { "type" : "string", "description" : "Position and number of coding bases (one based includes START and STOP codons)"},
        "aa_pos_aa_length" :     { "type" : "string", "description" : "Position and number of AA (one based, including START, but not STOP)"},
        "distance" :             { "type" : "string", "description" : "All items in this field are options, so the field could be empty. Up/Downstream: Distance to first / last codon Intergenic: Distance to closest gene Distance to closest Intron boundary in exon (+/- up/downstream). If same, use positive number. Distance to closest exon boundary in Intron (+/- up/downstream) Distance to first base in MOTIF Distance to first base in miRNA Distance to exon-intron boundary in splice_site or splice _region ChipSeq peak: Distance to summit (or peak center) Histone mark / Histone state: Distance to summit (or peak center)"},
        "errors_warnings_info" : { "type" : "string", "description" : "Errors, warnings or informative message that can affect annotation accuracy"}
        }