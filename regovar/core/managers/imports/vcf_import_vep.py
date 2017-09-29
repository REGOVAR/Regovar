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
        
        # Retrieve column mapping for column in vcf
        for col in Model.execute("SELECT name, name_ui, type FROM annotation_field WHERE database_uid='{}'".format(db_uid)):
            if col.name_ui in self.columns:
                columns_mapping[col.name_ui] = {'name': col.name, 'type': col.type, 'name_ui': col.name_ui}
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
                    col_mapping = self.columns_mapping[col_name]
                    sname = self.normalise_annotation_name(col_name)
                    fields = [sname]
                    vals = [self.escape_value_for_sql(data[col_pos])]
                    # Manage specials annotations
                    if sname == 'allele':
                        allele = vals[0].strip().strip('-') # When deletion, VEP use '-', but regovar just let empty string.
                        success, new_value = self.value_to_regovar_type(vals[0], "string")
                        vals = [new_value]
                    elif sname == 'feature':
                        trx_pk = vals[0].strip()
                        success, new_value = self.value_to_regovar_type(vals[0], "string")
                        vals = [new_value]
                    elif sname == 'consequence':
                        vals = ["ARRAY [{}]".format(",".join(["'{}'".format(self.escape_value_for_sql(v)) for v in data[col_pos].split('&')]))]
                    elif sname == "sift":
                        vals = vals[0].strip().split('(')
                        if len(vals) == 2:
                            fields = ["sift_pred", "sift_score"]
                            success, new_value = self.value_to_regovar_type(vals[0], "string")
                            vals = [new_value, float(vals[1][:-1])]
                        else:
                            continue
                    elif sname == "polyphen":
                        vals = vals[0].strip().split('(')
                        if len(vals) == 2:
                            fields = ["polyphen_pred", "polyphen_score"]
                            success, new_value = self.value_to_regovar_type(vals[0], "string")
                            vals = [new_value, float(vals[1][:-1])]
                        else:
                            continue
                    elif sname.endswith('maf'):
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
        "allele" :             { "type" : "string", "description" : "The variant allele used to calculate the consequence"},
        "gene" :               { "type" : "string", "description" : "Ensembl stable ID of affected gene"},
        "feature" :            { "type" : "string", "description" : "Ensembl stable ID of feature"},
        "feature_type" :       { "type" : "enum",   "description" : "Type of feature. Currently one of Transcript, RegulatoryFeature, MotifFeature"},
        "consequence" :        { "type" : "list", "description" : "Consequence type of this variant"},
        "cdna_position" :      { "type" : "string", "description" : "Relative position of base pair in cDNA sequence"},
        "cds_position" :       { "type" : "string", "description" : "Relative position of base pair in coding sequence"},
        "protein_position" :   { "type" : "string", "description" : "Relative position of amino acid in protein"},
        "amino_acids" :        { "type" : "string", "description" : "Only given if the variant affects the protein-coding sequence"},
        "codons" :             { "type" : "string", "description" : "The alternative codons with the variant base in upper case"},
        "pheno" :              { "type" : "string", "description" : "Indicates if existing variant is associated with a phenotype, disease or trait; multiple values correspond to multiple values in the Existing_variation field"},
        "existing_variation" : { "type" : "string", "description" : "Identifier(s) of co-located known variants"},
        "distance" :           { "type" : "string", "description" : "Shortest distance from variant to transcript"},
        "strand" :             { "type" : "string", "description" : "The DNA strand (1 or -1) on which the transcript/feature lies"},
        "symbol" :             { "type" : "string", "description" : "The gene symbol"},
        "symbol_source" :      { "type" : "string", "description" : "The source of the gene symbol"},
        "hgnc_id" :            { "type" : "string", "description" : "?"},
        "biotype" :            { "type" : "string", "description" : "Biotype of transcript or regulatory feature"},
        "canonical" :          { "type" : "bool",   "description" : "A flag indicating if the transcript is denoted as the canonical transcript for this gene"},
        "ccds" :               { "type" : "string", "description" : "The CCDS identifer for this transcript, where applicable"},
        "ensp" :               { "type" : "string", "description" : "The Ensembl protein identifier of the affected transcript"},
        "swissprot" :          { "type" : "string", "description" : "Best match UniProtKB/Swiss-Prot accession of protein product"},
        "trembl" :             { "type" : "string", "description" : "Best match UniProtKB/TrEMBL accession of protein product"},
        "uniparc" :            { "type" : "string", "description" : "Best match UniParc accession of protein product"},
        "sift_pred" :          { "type" : "string", "description" : "The SIFT prediction"},
        "sift_score" :         { "type" : "float",  "description" : "The SIFT score"},
        "polyphen_pred" :      { "type" : "string", "description" : "The PolyPhen prediction"},
        "polyphen_score" :     { "type" : "float",  "description" : "The PolyPhen prediction"},
        "exon" :               { "type" : "string", "description" : "The exon number (out of total number)"},
        "intron" :             { "type" : "string", "description" : "The intron number (out of total number)"},
        "domains" :            { "type" : "string",  "description" : "The source and identifer of any overlapping protein domains"},
        "hgvsc" :              { "type" : "string",  "description" : "The HGVS coding sequence name"},
        "hgvsp" :              { "type" : "string",  "description" : "The HGVS protein sequence name"},
        "hgvsg" :              { "type" : "string",  "description" : "The HGVS genomic sequence name"},
        "gmaf" :               { "type" : "float",   "description" : "Frequency of existing variant in 1000 Genomes"},   
        "afr_maf" :            { "type" : "float",   "description" : "Frequency of existing variant in 1000 Genomes combined African population"},  
        "amr_maf" :            { "type" : "float",   "description" : "Frequency of existing variant in 1000 Genomes combined American population"},  
        "asn_maf" :            { "type" : "float",   "description" : "Frequency of existing variant in 1000 Genomes combined Asian population"},  
        "eur_maf" :            { "type" : "float",   "description" : "Frequency of existing variant in 1000 Genomes combined European population"},  
        "eas_maf" :            { "type" : "float",   "description" : "Frequency of existing variant in 1000 Genomes combined East Asian population"},
        "sas_maf" :            { "type" : "float",   "description" : "Frequency of existing variant in 1000 Genomes combined South Asian population"},
        "aa_maf" :             { "type" : "float",   "description" : "Frequency of existing variant in NHLBI-ESP African American population"},  
        "ea_maf" :             { "type" : "float",   "description" : "Frequency of existing variant in NHLBI-ESP European American population"},  
        "clin_sig" :           { "type" : "string",  "description" : "ClinVar clinical significance of the dbSNP variant"},
        "somatic" :            { "type" : "string",  "description" : "Somatic status of existing variant(s); multiple values correspond to multiple values in the Existing_variation field"},
        "pubmed" :             { "type" : "string",  "description" : "Pubmed ID(s) of publications that cite existing variant"},
        "motif_name" :         { "type" : "string",  "description" : "The source and identifier of a transcription factor binding profile aligned at this position"},
        "motif_pos" :          { "type" : "string",  "description" : "The relative position of the variation in the aligned TFBP"},
        "high_inf_pos" :       { "type" : "bool",    "description" : "A flag indicating if the variant falls in a high information position of a transcription factor binding profile (TFBP)"},
        "motif_score_change" : { "type" : "string",  "description" : "The difference in motif score of the reference and variant sequences for the TFBP"},
        "impact" :             { "type" : "string", "description" : "The impact modifier for the consequence type"},
        "variant_class" :      { "type" : "string", "description" : "Sequence Ontology variant class"},
        "tsl" :                { "type" : "string", "description" : "Transcript support level. NB: not available for GRCh37"},
        "appris" :             { "type" : "string", "description" : "Annotates alternatively spliced transcripts as primary or alternate based on a range of computational methods. NB: not available for GRCh37"},
        "refseq_match" :       { "type" : "string", "description" : "The RefSeq transcript match status; contains a number of flags indicating whether this RefSeq transcript matches the underlying reference sequence and/or an Ensembl transcript (more information). NB: not available for GRCh37"},
        "gene_pheno" :         { "type" : "string", "description" : "Indicates if overlapped gene is associated with a phenotype, disease or trait"},
        "hgvs_offset" :        { "type" : "int",    "description" : "Indicates by how many bases the HGVS notations for this variant have been shifted"},
        "exac_maf" :           { "type" : "float", "description" : "Frequency of existing variant in Exac database"},
        "exac_adj_maf" :       { "type" : "float", "description" : "Frequency in ? population (Exac database)"},
        "exac_afr_maf" :       { "type" : "float", "description" : "Frequency in African population (Exac database)"},
        "exac_amr_maf" :       { "type" : "float", "description" : "Frequency in American population (Exac database)"},
        "exac_eas_maf" :       { "type" : "float", "description" : "Frequency in East Asian population (Exac database)"},
        "exac_fin_maf" :       { "type" : "float", "description" : "Frequency in ? population (Exac database)"},
        "exac_nfe_maf" :       { "type" : "float", "description" : "Frequency in ? population (Exac database)"},
        "exac_oth_maf" :       { "type" : "float", "description" : "Frequency in ? population (Exac database)"},
        "exac_sas_maf" :       { "type" : "float", "description" : "Frequency in South Asian population (Exac database)"}
        }