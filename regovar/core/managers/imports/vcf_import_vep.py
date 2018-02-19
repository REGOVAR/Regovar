#!env/python3
# coding: utf-8

import ipdb
import sqlalchemy

from core.managers.imports.abstract_import_manager import AbstractTranscriptDataImporter
from core.framework.common import *
import core.model as Model


class VepImporter(AbstractTranscriptDataImporter): 
    
    
    # ===========================================================================================================
    # VEP IMPORT METHODS 
    # ===========================================================================================================
        
    def init(self, headers, reference_id):
        """
            Check VCF headers and return true if VEP data can be imported; false otherwise
            By the way, when VEP data are here, init internal data of the importer
        """
        result = False
        
        
        if 'VEP' in headers.keys() :
            vcf_flag = None
            if 'CSQ' in headers['INFO'].keys():
                vcf_flag = 'CSQ'
            elif 'ANN' in headers['INFO'].keys():
                vcf_flag = 'ANN'
                
            if vcf_flag :
                reference_name = Model.execute("SELECT table_suffix FROM reference WHERE id={}".format(reference_id)).first()[0]
                
                data = headers['INFO'][vcf_flag]['description'].split('Format:')
                self.name = "VEP"
                self.reference_id = reference_id
                self.description = data[0].strip()
                self.columns = [self.normalise_annotation_name(c).title() for c in data[1].strip().split('|')]
                self.version = headers['VEP'][0].split(' ')[0]
                self.table_name = self.normalise_annotation_name('{}_{}_{}'.format('VEP', self.version, reference_name))
                self.vcf_flag = vcf_flag
                self.columns_definitions = VepImporter.columns_definitions
                result = 'Feature' in self.columns
                
                if result:
                    self.check_annotation_table()

        print("VEP init : ", result)
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
        
        # # Pre-process of polyphen/sift vcf columns that are split on 2 columns in regovar db
        # self.columns = [self.normalise_annotation_name(s) for s in self.columns]
        # if "sift" in self.columns: 
        #     self.columns.extend(["sift_pred", "sift_score"])
        #     self.columns.remove("sift")
        # if "polyphen" in self.columns: 
        #     self.columns.extend(["polyphen_pred", "polyphen_score"])
        #     self.columns.remove("polyphen")

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

                    if not col_mapping and col_name not in ['sift', 'polyphen']:
                        # war("Unable to import vcf VEP annotation : {} ({}). No column mapping/definition provided. SKIPPED".format(col_name, ','.join(vals)))
                        continue
                    
                    # Manage specials annotations
                    if col_name == 'allele':
                        allele = vals[0].strip().strip('-') # When deletion, VEP use '-', but regovar just let empty string.
                        success, new_value = self.value_to_regovar_type(vals[0], "string")
                        vals = [new_value]
                    elif col_name == 'feature':
                        trx_pk = vals[0].strip()
                        success, new_value = self.value_to_regovar_type(vals[0], "string")
                        vals = [new_value]
                    elif col_name == 'consequence':
                        vals = ["ARRAY [{}]".format(",".join(["'{}'".format(self.escape_value_for_sql(v)) for v in data[col_pos].split('&')]))]
                    elif col_name == "sift":
                        vals = vals[0].strip().split('(')
                        if len(vals) == 2:
                            fields = ["sift_pred", "sift_score"]
                            success, new_value = self.value_to_regovar_type(vals[0], "string")
                            vals = [new_value, float(vals[1][:-1])]
                        else:
                            continue
                    elif col_name == "polyphen":
                        vals = vals[0].strip().split('(')
                        if len(vals) == 2:
                            fields = ["polyphen_pred", "polyphen_score"]
                            success, new_value = self.value_to_regovar_type(vals[0], "string")
                            vals = [new_value, float(vals[1][:-1])]
                        else:
                            continue
                    elif col_name.endswith('maf'):
                        v = vals[0]
                        vals = [None]
                        v = v.strip().split('&')
                        if len(v) > 0:
                            v = v[0].strip().split(':')
                            if len(v) == 2 and alt == v[0]:
                                vals = [float(v[1])]
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
        "allele" :             { "type" : "string", "order":  1, "description" : "The variant allele used to calculate the consequence."},
        "amino_acids" :        { "type" : "string", "order":  2, "description" : "Only given if the variant affects the protein-coding sequence."},
        "appris" :             { "type" : "string", "order":  3, "description" : "Annotates alternatively spliced transcripts as primary or alternate based on a range of computational methods. NB: not available for GRCh37."},
        "biotype" :            { "type" : "string", "order":  4, "description" : "Biotype of transcript or regulatory feature."},
        "canonical" :          { "type" : "bool",   "order":  5, "description" : "A flag indicating if the transcript is denoted as the canonical transcript for this gene."},
        "ccds" :               { "type" : "string", "order":  6, "description" : "The CCDS identifer for this transcript, where applicable."},
        "cdna_position" :      { "type" : "string", "order":  7, "description" : "Relative position of base pair in cDNA sequence."},
        "cds_position" :       { "type" : "string", "order":  8, "description" : "Relative position of base pair in coding sequence."},
        "clin_sig" :           { "type" : "string", "order":  9, "description" : "ClinVar clinical significance of the dbSNP variant."},
        "codons" :             { "type" : "string", "order": 10, "description" : "The alternative codons with the variant base in upper case."},
        "consequence" :        { "type" : "list",   "order": 11, "description" : "Consequence type of this variant."},
        "distance" :           { "type" : "string", "order": 12, "description" : "Shortest distance from variant to transcript."},
        "domains" :            { "type" : "string", "order": 13, "description" : "The source and identifer of any overlapping protein domains."},
        "ensp" :               { "type" : "string", "order": 14, "description" : "The Ensembl protein identifier of the affected transcript."},
        "existing_variation" : { "type" : "string", "order": 15, "description" : "Identifier(s) of co-located known variants."},
        "exon" :               { "type" : "string", "order": 16, "description" : "The exon number (out of total number)."},
        "feature" :            { "type" : "string", "order": 17, "description" : "Ensembl stable ID of feature."},
        "feature_type" :       { "type" : "enum",   "order": 18, "description" : "Type of feature. Currently one of Transcript, RegulatoryFeature, MotifFeature."},
        "gene" :               { "type" : "string", "order": 19, "description" : "Ensembl stable ID of affected gene."},
        "gene_pheno" :         { "type" : "string", "order": 20, "description" : "Indicates if overlapped gene is associated with a phenotype, disease or trait."},
        "hgnc_id" :            { "type" : "string", "order": 21, "description" : "Id of the gene in HUGO (Gene Nomenclature Committee)."},
        "hgvs_offset" :        { "type" : "int",    "order": 22, "description" : "Indicates by how many bases the HGVS notations for this variant have been shifted."},
        "hgvsc" :              { "type" : "string", "order": 23, "description" : "The HGVS coding sequence name."},
        "hgvsp" :              { "type" : "string", "order": 24, "description" : "The HGVS protein sequence name."},
        "hgvsg" :              { "type" : "string", "order": 25, "description" : "The HGVS genomic sequence name."},
        "high_inf_pos" :       { "type" : "bool",   "order": 26, "description" : "A flag indicating if the variant falls in a high information position of a transcription factor binding profile (TFBP)."},
        "impact" :             { "type" : "string", "order": 27, "description" : "The impact modifier for the consequence type."},
        "intron" :             { "type" : "string", "order": 28, "description" : "The intron number (out of total number)."},
        "motif_name" :         { "type" : "string", "order": 29, "description" : "The source and identifier of a transcription factor binding profile aligned at this position."},
        "motif_pos" :          { "type" : "string", "order": 30, "description" : "The relative position of the variation in the aligned TFBP."},
        "motif_score_change" : { "type" : "string", "order": 31, "description" : "The difference in motif score of the reference and variant sequences for the TFBP."},
        "pheno" :              { "type" : "string", "order": 32, "description" : "Indicates if existing variant is associated with a phenotype, disease or trait; multiple values correspond to multiple values in the Existing_variation field."},
        "polyphen_pred" :      { "type" : "string", "order": 33, "description" : "The PolyPhen prediction."},
        "polyphen_score" :     { "type" : "float",  "order": 34, "description" : "The PolyPhen prediction."},
        "protein_position" :   { "type" : "string", "order": 35, "description" : "Relative position of amino acid in protein."},
        "pubmed" :             { "type" : "string", "order": 36, "description" : "Pubmed ID(s) of publications that cite existing variant."},
        "refseq" :             { "type" : "string", "order": 37, "description" : "The RefSeq transcript match."},
        "refseq_match" :       { "type" : "string", "order": 38, "description" : "The RefSeq transcript match status; contains a number of flags indicating whether this RefSeq transcript matches the underlying reference sequence and/or an Ensembl transcript (more information). NB: not available for GRCh37."},
        "sift_pred" :          { "type" : "string", "order": 39, "description" : "The SIFT prediction."},
        "sift_score" :         { "type" : "float",  "order": 40, "description" : "The SIFT score."},
        "somatic" :            { "type" : "string", "order": 41, "description" : "Somatic status of existing variant(s); multiple values correspond to multiple values in the Existing_variation field."},
        "strand" :             { "type" : "string", "order": 42, "description" : "The DNA strand (1 or -1) on which the transcript/feature lies."},
        "swissprot" :          { "type" : "string", "order": 43, "description" : "Best match UniProtKB/Swiss-Prot accession of protein product."},
        "symbol" :             { "type" : "string", "order": 44, "description" : "The gene symbol."},
        "symbol_source" :      { "type" : "string", "order": 45, "description" : "The source of the gene symbol."},
        "trembl" :             { "type" : "string", "order": 46, "description" : "Best match UniProtKB/TrEMBL accession of protein product."},
        "tsl" :                { "type" : "string", "order": 47, "description" : "Transcript support level. NB: not available for GRCh37."},
        "uniparc" :            { "type" : "string", "order": 48, "description" : "Best match UniParc accession of protein product."},
        "variant_class" :      { "type" : "string", "order": 49, "description" : "Sequence Ontology variant class."},
        "gmaf" :               { "type" : "float",  "order": 50, "description" : "Frequency of existing variant in 1000 Genomes."},   
        "afr_maf" :            { "type" : "float",  "order": 51, "description" : "Frequency of existing variant in 1000 Genomes combined African population."},  
        "amr_maf" :            { "type" : "float",  "order": 52, "description" : "Frequency of existing variant in 1000 Genomes combined American population."},  
        "asn_maf" :            { "type" : "float",  "order": 53, "description" : "Frequency of existing variant in 1000 Genomes combined Asian population."},  
        "eur_maf" :            { "type" : "float",  "order": 54, "description" : "Frequency of existing variant in 1000 Genomes combined European population."},  
        "eas_maf" :            { "type" : "float",  "order": 55, "description" : "Frequency of existing variant in 1000 Genomes combined East Asian population."},
        "sas_maf" :            { "type" : "float",  "order": 56, "description" : "Frequency of existing variant in 1000 Genomes combined South Asian population."},
        "exac_maf" :           { "type" : "float",  "order": 57, "description" : "Frequency of existing variant in Exac database."},
        "exac_adj_maf" :       { "type" : "float",  "order": 58, "description" : "Adjusted minor allelle frequency (Exac database)."},
        "exac_afr_maf" :       { "type" : "float",  "order": 59, "description" : "Frequency in African population (Exac database)."},
        "exac_amr_maf" :       { "type" : "float",  "order": 60, "description" : "Frequency in American population (Exac database)."},
        "exac_eas_maf" :       { "type" : "float",  "order": 61, "description" : "Frequency in East Asian population (Exac database)."},
        "exac_fin_maf" :       { "type" : "float",  "order": 62, "description" : "Frequency in Finnish population (Exac database)."},
        "exac_nfe_maf" :       { "type" : "float",  "order": 63, "description" : "Frequency in Non-Finnish European population (Exac database)."},
        "exac_oth_maf" :       { "type" : "float",  "order": 64, "description" : "Frequency in Other population (Exac database)."},
        "exac_sas_maf" :       { "type" : "float",  "order": 65, "description" : "Frequency in South Asian population (Exac database)."},
        "aa_maf" :             { "type" : "float",  "order": 66, "description" : "Frequency of existing variant in NHLBI-ESP African American population."},  
        "ea_maf" :             { "type" : "float",  "order": 67, "description" : "Frequency of existing variant in NHLBI-ESP European American population."}
        }