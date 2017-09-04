#!env/python3
# coding: utf-8

import ipdb




class VepImporter:
    table_name = ""
    version = ""
    columns = []
    
    def escape_value_for_sql(value):
        if type(value) is str:
            value = value.replace('%', '%%')
            value = value.replace("'", "''")

            # Workaround for some wrong annotations found
            value = value.replace('-:0', '-: 0')   # VEP aa_maf = "-:0.1254..."
        return value
        
    def init(header_description):
        d = header_description.split('Format:')
        VepImporter.columns = d[1].strip().split('|')
        print("VEP init : ", VepImporter.columns)
    
    def create_annotation_table(vcf_headers):
        pass

    def import_annotations(bin, chrm, pos, ref, alt, annotations):
        print("VEP import : ", VepImporter.columns) #, bin, chrm, pos, ref, alt, annotations)
        return "", 0
    
        #for info in annotations:
            #data = info.split('|')
            #q_fields = []
            #q_values = []
            #allele   = ""
            #trx_pk = "NULL"
            
            #for col_pos, col_name in enumerate(VepImporter.columns):
                #q_fields.append(metadata['db_map'][col_name]['name'])
                #val = VepImporter.escape_value_for_sql(data[col_pos])
                
                ## Manage specials annotations
                #if col_name == 'Allele':
                    #allele = val.strip().strip('-') # When deletion, VEP use '-', but regovar just let empty string.
                #elif col_name == 'Feature':
                    #trx_pk = val.strip()
                #elif col_name == 'Consequence':
                    #val = "ARRAY [{}]".format(",".join([VepImporter.escape_value_for_sql(v) for v in data[col_pos].split('&')]))
                    

                #q_values.append('\'{}\''.format(val) if val != '' and val is not None else 'NULL')

            #pos, ref, alt = normalize(row.pos, row.ref, sp.alleles[0])
            ## print(pos, ref, alt, allele)
            #if pos is not None and alt==allele and len(q_fields) > 0:
                ## print("ok")
                #sql_query3 += sql_annot_trx.format(metadata['table'], ','.join(q_fields), ','.join(q_values), bin, chrm, pos, ref, alt, trx_pk)
                #count += 1
            #pos, ref, alt = normalize(row.pos, row.ref, sp.alleles[1])
            ## print(pos, ref, alt, allele)
            #if pos is not None and alt==allele and len(q_fields) > 0:
                ## print("ok")
                #sql_query3 += sql_annot_trx.format(metadata['table'], ','.join(q_fields), ','.join(q_values), bin, chrm, pos, ref, alt, trx_pk)
                #count += 1
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # When need to create annotation table/field : to create columns with good type and description
    columns_definitions = {
        "allele" :             { "type" : "string", "description" : "the variant allele used to calculate the consequence"},
        "gene" :               { "type" : "string", "description" : "Ensembl stable ID of affected gene"},
        "feature" :            { "type" : "string", "description" : "Ensembl stable ID of feature"},
        "feature_type" :       { "type" : "enum",   "description" : "type of feature. Currently one of Transcript, RegulatoryFeature, MotifFeature"},
        "consequence" :        { "type" : "[enum]", "description" : "consequence type of this variant"},
        "cdna_position" :      { "type" : "string", "description" : "relative position of base pair in cDNA sequence"},
        "cds_position" :       { "type" : "string", "description" : "relative position of base pair in coding sequence"},
        "protein_position" :   { "type" : "string", "description" : "relative position of amino acid in protein"},
        "amino_acids" :        { "type" : "string", "description" : "only given if the variant affects the protein-coding sequence"},
        "codons" :             { "type" : "string", "description" : "the alternative codons with the variant base in upper case"},
        "existing_variation" : { "type" : "string", "description" : "?"},
        "distance" :           { "type" : "string", "description" : "Shortest distance from variant to transcript"},
        "strand" :             { "type" : "string", "description" : "the DNA strand (1 or -1) on which the transcript/feature lies"},
        "symbol" :             { "type" : "string", "description" : "the gene symbol"},
        "symbol_source" :      { "type" : "string", "description" : "the source of the gene symbol"},
        "hgnc_id" :            { "type" : "string", "description" : "?"},
        "biotype" :            { "type" : "string", "description" : "Biotype of transcript or regulatory feature"},
        "canonical" :          { "type" : "bool",   "description" : "a flag indicating if the transcript is denoted as the canonical transcript for this gene"},
        "ccds" :               { "type" : "string", "description" : "the CCDS identifer for this transcript, where applicable"},
        "ensp" :               { "type" : "string", "description" : "the Ensembl protein identifier of the affected transcript"},
        "swissprot" :          { "type" : "string", "description" : "Best match UniProtKB/Swiss-Prot accession of protein product"},
        "trembl" :             { "type" : "string", "description" : "Best match UniProtKB/TrEMBL accession of protein product"},
        "uniparc" :            { "type" : "string", "description" : "Best match UniParc accession of protein product"},
        "refseq" :             { "type" : "string", "description" : "?"},
        "sift" :               { "type" : "string", "description" : "the SIFT prediction and/or score, with both given as prediction(score)"},
            #-> sift pred
            #-> sift score
        "polyphen" :           { "type" : "string", "description" : "the PolyPhen prediction and/or score"},
            #-> poly pred
            #-> poly score
        "exon" :               { "type" : "string", "description" : "the exon number (out of total number)"},
            #-> exon pos
            #-> exon total
        "intron" :             { "type" : "string", "description" :"the intron number (out of total number)"},
            #-> intron pos
            #-> intron total
        "domains" :            { "type" : "string", "description" : "the source and identifer of any overlapping protein domains"},
        "hgvsc" :              { "type" : "string", "description" : "the HGVS coding sequence name"},
        "hgvsp" :              { "type" : "string", "description" : "the HGVS protein sequence name"},
        "hgvsg" :              { "type" : "string", "description" : "the HGVS genomic sequence name"},
        "gmaf" :               { "type" : "float",  "description" : "?"},   
        "afr_maf" :            { "type" : "float",  "description" : "?"},  
        "amr_maf" :            { "type" : "float",  "description" : "?"},  
        "asn_maf" :            { "type" : "float",  "description" : "?"},  
        "eur_maf" :            { "type" : "float",  "description" : "?"},  
        "aa_maf" :             { "type" : "float",  "description" : "?"},  
        "ea_maf" :             { "type" : "float",  "description" : "?"},  
        "clin_sig" :           { "type" : "string", "description" : "ClinVar clinical significance of the dbSNP variant"},
        "somatic" :            { "type" : "lst<str>","description" : "Somatic status of existing variant(s); multiple values correspond to multiple values in the Existing_variation field"},
        "pubmed" :             { "type" : "lst<str>","description" : "Pubmed ID(s) of publications that cite existing variant"},
        "motif_name" :         { "type" : "string",  "description" : "the source and identifier of a transcription factor binding profile aligned at this position"},
        "motif_pos" :          { "type" : "string",  "description" : "The relative position of the variation in the aligned TFBP"},
        "high_inf_pos" :       { "type" : "bool",    "description" : "a flag indicating if the variant falls in a high information position of a transcription factor binding profile (TFBP)"},
        "motif_score_change" : { "type" : "string",  "description" : "The difference in motif score of the reference and variant sequences for the TFBP"}
        }