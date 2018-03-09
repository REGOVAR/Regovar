 
-- Import csv data
CREATE TABLE import_refgene_hg19
(
    bin integer,
    name character varying(255) COLLATE pg_catalog."C",
    chrom character varying(255) COLLATE pg_catalog."C",
    strand character(1),
    trxstart bigint,
    trxend bigint,
    cdsstart bigint,
    cdsend bigint,
    exoncount bigint,
    exonstarts text,
    exonends text,
    score bigint,
    name2 character varying(255) COLLATE pg_catalog."C",
    cdsstartstat character varying(255) COLLATE pg_catalog."C",
    cdsendstat character varying(255) COLLATE pg_catalog."C",
    exonframes text
);
CREATE TABLE import_refgene_hg38
(
    bin integer,
    name character varying(255) COLLATE pg_catalog."C",
    chrom character varying(255) COLLATE pg_catalog."C",
    strand character(1),
    trxstart bigint,
    trxend bigint,
    cdsstart bigint,
    cdsend bigint,
    exoncount bigint,
    exonstarts text,
    exonends text,
    score bigint,
    name2 character varying(255) COLLATE pg_catalog."C",
    cdsstartstat character varying(255) COLLATE pg_catalog."C",
    cdsendstat character varying(255) COLLATE pg_catalog."C",
    exonframes text
);
\COPY import_refgene_hg19 FROM '/var/regovar/databases/hg19/refGene.txt' DELIMITER E'\t' CSV;
\COPY import_refgene_hg38 FROM '/var/regovar/databases/hg38/refGene.txt' DELIMITER E'\t' CSV;
   
   
   

--
-- Exon table for Hg19
--
-- Create refgene_exon_hg19 table
CREATE TABLE refgene_exon_hg19
(
    bin integer NOT NULL,
    chr integer,
    exonpos int,
    exoncount int,
    exonrange int8range,
    i_exonstart character varying(255),
    i_exonend character varying(255),
    i_exonstarts character varying(10)[]
);
-- Populate refgene_exon_hg19 table
INSERT INTO refgene_exon_hg19(bin, chr, exoncount, i_exonstart, i_exonend, i_exonstarts)
SELECT bin, 
    CASE WHEN chrom='chrX' THEN 23 WHEN chrom='chrY' THEN 24 WHEN chrom='chrM' THEN 25 ELSE CAST(substring(chrom from 4) AS INTEGER) END,
    exoncount,
    unnest(string_to_array(trim(trailing ',' from exonstarts), ',')), 
    unnest(string_to_array(trim(trailing ',' from exonends), ',')), 
    string_to_array(trim(trailing ',' from exonstarts), ',')
FROM import_refgene_hg19
WHERE char_length(chrom) <= 5;
UPDATE refgene_exon_hg19 SET 
    exonrange=int8range(CAST(coalesce(i_exonstart, '0') AS integer), CAST(coalesce(i_exonend, '0') AS integer)),
    exonpos=array_search(CAST(i_exonstart AS character varying(10)), i_exonstarts) ;
-- Clean
ALTER TABLE refgene_exon_hg19 DROP COLUMN i_exonstart;
ALTER TABLE refgene_exon_hg19 DROP COLUMN i_exonend;
ALTER TABLE refgene_exon_hg19 DROP COLUMN i_exonstarts;
DROP TABLE IF EXISTS import_refgene_hg19;
-- Create indexes  
CREATE INDEX refgene_exon_hg19_chrom_exonange_idx
    ON refgene_exon_hg19
    USING btree (bin, chr, exonrange);
CREATE INDEX refgene_exon_hg19_exonange_idx
    ON refgene_exon_hg19
    USING gist (exonrange);
    
    
--
-- Exon table for Hg38
--
-- Create refgene_exon_hg38 table
CREATE TABLE refgene_exon_hg38
(
    bin integer NOT NULL,
    chr integer,
    exonpos int,
    exoncount int,
    exonrange int8range,
    i_exonstart character varying(255),
    i_exonend character varying(255),
    i_exonstarts character varying(10)[]
);  
-- Populate refgene_exon_hg38 table
INSERT INTO refgene_exon_hg38(bin, chr, exoncount, i_exonstart, i_exonend, i_exonstarts)
SELECT bin, 
    CASE WHEN chrom='chrX' THEN 23 WHEN chrom='chrY' THEN 24 WHEN chrom='chrM' THEN 25 ELSE CAST(substring(chrom from 4) AS INTEGER) END,
    exoncount,
    unnest(string_to_array(trim(trailing ',' from exonstarts), ',')), 
    unnest(string_to_array(trim(trailing ',' from exonends), ',')), 
    string_to_array(trim(trailing ',' from exonstarts), ',')
FROM import_refgene_hg38
WHERE char_length(chrom) <= 5;
UPDATE refgene_exon_hg38 SET 
    exonrange=int8range(CAST(coalesce(i_exonstart, '0') AS integer), CAST(coalesce(i_exonend, '0') AS integer)),
    exonpos=array_search(CAST(i_exonstart AS character varying(10)), i_exonstarts) ;
-- Clean
ALTER TABLE refgene_exon_hg38 DROP COLUMN i_exonstart;
ALTER TABLE refgene_exon_hg38 DROP COLUMN i_exonend;
ALTER TABLE refgene_exon_hg38 DROP COLUMN i_exonstarts; 
DROP TABLE IF EXISTS import_refgene_hg38;
-- Create indexes
CREATE INDEX refgene_exon_hg38_chrom_exonange_idx
    ON refgene_exon_hg38
    USING btree (bin, chr, exonrange);
CREATE INDEX refgene_exon_hg38_exonange_idx
    ON refgene_exon_hg38
    USING gist (exonrange);
    
--
-- Adding new precomputed field
--
INSERT INTO public.annotation_field(database_uid, ord, name, name_ui, type, description, meta) 
VALUES('2c0a7043a9e736eaf14b6614fff102c0', 9, 'is_exonic', 'Exonic', 'bool', 'Exonic variant (based on refGen database).', NULL);
-- Regen field uid
UPDATE annotation_field SET uid=MD5(concat(database_uid, name));

-- Update database version
UPDATE parameter SET value='7.0' WHERE key='database_version';

