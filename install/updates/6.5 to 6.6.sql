
CREATE FUNCTION upgrade_db(current_version text)
RETURNS void AS $$
BEGIN
    IF current_version = '6.5' THEN
        -- New field VAF
        INSERT INTO annotation_field (database_uid, ord, name, name_ui, type, description, meta) VALUES ('492f18b60811bf85ce118c0c6a1a5c4a', 13, 's{}_vaf', 'VAF', 'sample_array', 'Variant allelic frequence. (1=100%)', '{"type": "float"}');
        -- Update fields orders
        UPDATE annotation_field SET ord=14 WHERE name='s{}_qual';
        UPDATE annotation_field SET ord=15 WHERE name='s{}_filter';
        -- Regen field uid (for VAF)
        UPDATE annotation_field SET uid=MD5(concat(database_uid, name));
        
        -- Fix QRegovar #154: Replace GT by Genotype
        UPDATE annotation_field SET name_ui='Genotype' WHERE name='s{}_gt';
        
        
        -- fix QRegovar #127: default order for VEP field
        UPDATE annotation_field SET ord=1 WHERE name='allele';
        UPDATE annotation_field SET ord=3 WHERE name='amino_acids';
        UPDATE annotation_field SET ord=4 WHERE name='appris';
        UPDATE annotation_field SET ord=5 WHERE name='biotype';
        UPDATE annotation_field SET ord=6 WHERE name='canonical';
        UPDATE annotation_field SET ord=7 WHERE name='ccds';
        UPDATE annotation_field SET ord=8 WHERE name='cdna_position';
        UPDATE annotation_field SET ord=9 WHERE name='cds_position';
        UPDATE annotation_field SET ord=10 WHERE name='clin_sig';
        UPDATE annotation_field SET ord=11 WHERE name='codons';
        UPDATE annotation_field SET ord=12 WHERE name='consequence';
        UPDATE annotation_field SET ord=13 WHERE name='distance';
        UPDATE annotation_field SET ord=14 WHERE name='domains';
        UPDATE annotation_field SET ord=15 WHERE name='ensp';
        UPDATE annotation_field SET ord=16 WHERE name='existing_variation';
        UPDATE annotation_field SET ord=17 WHERE name='exon';
        UPDATE annotation_field SET ord=18 WHERE name='feature';
        UPDATE annotation_field SET ord=19 WHERE name='feature_type';
        UPDATE annotation_field SET ord=20 WHERE name='gene';
        UPDATE annotation_field SET ord=21 WHERE name='gene_pheno';
        UPDATE annotation_field SET ord=22 WHERE name='hgnc_id';
        UPDATE annotation_field SET ord=23 WHERE name='hgvs_offset';
        UPDATE annotation_field SET ord=24 WHERE name='hgvsc';
        UPDATE annotation_field SET ord=25 WHERE name='hgvsp';
        UPDATE annotation_field SET ord=26 WHERE name='hgvsg';
        UPDATE annotation_field SET ord=27 WHERE name='high_inf_pos';
        UPDATE annotation_field SET ord=28 WHERE name='impact';
        UPDATE annotation_field SET ord=29 WHERE name='intron';
        UPDATE annotation_field SET ord=30 WHERE name='motif_name';
        UPDATE annotation_field SET ord=31 WHERE name='motif_pos';
        UPDATE annotation_field SET ord=32 WHERE name='motif_score_change';
        UPDATE annotation_field SET ord=33 WHERE name='pheno';
        UPDATE annotation_field SET ord=34 WHERE name='polyphen_pred';
        UPDATE annotation_field SET ord=35 WHERE name='polyphen_score';
        UPDATE annotation_field SET ord=36 WHERE name='protein_position';
        UPDATE annotation_field SET ord=37 WHERE name='pubmed';
        UPDATE annotation_field SET ord=38 WHERE name='refseq';
        UPDATE annotation_field SET ord=39 WHERE name='refseq_match';
        UPDATE annotation_field SET ord=40 WHERE name='sift_pred';
        UPDATE annotation_field SET ord=41 WHERE name='sift_score';
        UPDATE annotation_field SET ord=42 WHERE name='somatic';
        UPDATE annotation_field SET ord=43 WHERE name='strand';
        UPDATE annotation_field SET ord=44 WHERE name='swissprot';
        UPDATE annotation_field SET ord=45 WHERE name='symbol';
        UPDATE annotation_field SET ord=46 WHERE name='symbol_source';
        UPDATE annotation_field SET ord=47 WHERE name='trembl';
        UPDATE annotation_field SET ord=48 WHERE name='tsl';
        UPDATE annotation_field SET ord=49 WHERE name='uniparc';
        UPDATE annotation_field SET ord=50 WHERE name='variant_class';
        UPDATE annotation_field SET ord=51 WHERE name='gmaf';
        UPDATE annotation_field SET ord=52 WHERE name='afr_maf';
        UPDATE annotation_field SET ord=53 WHERE name='amr_maf';
        UPDATE annotation_field SET ord=54 WHERE name='asn_maf';
        UPDATE annotation_field SET ord=55 WHERE name='eur_maf';
        UPDATE annotation_field SET ord=56 WHERE name='eas_maf';
        UPDATE annotation_field SET ord=57 WHERE name='sas_maf';
        UPDATE annotation_field SET ord=58 WHERE name='exac_maf';
        UPDATE annotation_field SET ord=59 WHERE name='exac_adj_maf';
        UPDATE annotation_field SET ord=60 WHERE name='exac_afr_maf';
        UPDATE annotation_field SET ord=61 WHERE name='exac_amr_maf';
        UPDATE annotation_field SET ord=62 WHERE name='exac_eas_maf';
        UPDATE annotation_field SET ord=63 WHERE name='exac_fin_maf';
        UPDATE annotation_field SET ord=64 WHERE name='exac_nfe_maf';
        UPDATE annotation_field SET ord=65 WHERE name='exac_oth_maf';
        UPDATE annotation_field SET ord=66 WHERE name='exac_sas_maf';
        UPDATE annotation_field SET ord=67 WHERE name='aa_maf';
        UPDATE annotation_field SET ord=68 WHERE name='ea_maf';
        
        -- Update VEP field description
        UPDATE annotation_field SET description='Adjusted minor allelle frequency (Exac database).' WHERE name='exac_adj_maf';
        UPDATE annotation_field SET description='Frequency in African population (Exac database).' WHERE name='exac_afr_maf';
        UPDATE annotation_field SET description='Frequency in American population (Exac database).' WHERE name='exac_amr_maf';
        UPDATE annotation_field SET description='Frequency in East Asian population (Exac database).' WHERE name='exac_eas_maf';
        UPDATE annotation_field SET description='Frequency in Finnish population (Exac database).' WHERE name='exac_fin_maf';
        UPDATE annotation_field SET description='Frequency in Non-Finnish European population (Exac database).' WHERE name='exac_nfe_maf';
        UPDATE annotation_field SET description='Frequency in Other population (Exac database).' WHERE name='exac_oth_maf';
        UPDATE annotation_field SET description='Frequency in South Asian population (Exac database).' WHERE name='exac_sas_maf';
        UPDATE annotation_field SET description='Id of the gene in HUGO (Gene Nomenclature Committee).' WHERE name='hgnc_id';
        
        -- Update database version
        UPDATE parameter SET value='6.6' WHERE key='database_version';
    END IF; 
END;
$$
LANGUAGE 'plpgsql' ;


SELECT upgrade_db(value) FROM parameter WHERE key='database_version';
