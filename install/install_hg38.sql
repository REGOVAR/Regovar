

--
-- Regovar Database tables
--
INSERT INTO reference(id, name, description, url, table_suffix) VALUES (3, 'Hg38', 'Human Genom version 38', 'http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/', 'hg38');
CREATE TABLE variant_hg38
(
    id bigserial NOT NULL,
    bin integer,
    chr integer,
    pos bigint NOT NULL,
    ref text NOT NULL,
    alt text NOT NULL,
    is_transition boolean,
    sample_list integer[],
    regovar_score smallint,
    regovar_score_meta JSON,
    CONSTRAINT variant_hg38_pkey PRIMARY KEY (id),
    CONSTRAINT variant_hg38_ukey UNIQUE (chr, pos, ref, alt)
);
CREATE TABLE sample_variant_hg38
(
    sample_id integer NOT NULL,
    bin integer,
    chr integer,
    pos bigint NOT NULL,
    ref text NOT NULL,
    alt text NOT NULL,
    variant_id bigint,
    vcf_line bigint,
    genotype integer,
    depth integer,
    depth_alt integer,
    quality real,
    filter JSON,
    infos character varying(255)[][] COLLATE pg_catalog."C",
    mosaic real,
    is_composite boolean DEFAULT False,
    CONSTRAINT sample_variant_hg38_pkey PRIMARY KEY (sample_id, chr, pos, ref, alt),
    CONSTRAINT sample_variant_hg38_ukey UNIQUE (sample_id, variant_id)
);
CREATE INDEX sample_variant_hg38_idx_id
  ON sample_variant_hg38
  USING btree
  (variant_id);
CREATE INDEX sample_variant_hg38_idx_samplevar
  ON sample_variant_hg38
  USING btree
  (sample_id);
CREATE INDEX sample_variant_hg38_idx_site
  ON sample_variant_hg38
  USING btree
  (sample_id, bin, chr, pos);
CREATE INDEX variant_hg38_idx_id
  ON variant_hg38
  USING btree
  (id);
CREATE INDEX variant_hg38_idx_site
  ON variant_hg38
  USING btree
  (bin, chr, pos);




--
-- Import csv data
--
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


\COPY import_refgene_hg38 FROM '/var/regovar/databases/hg38/refGene.txt' DELIMITER E'\t' CSV;









--
-- Create regovar tables for refgene data
--
CREATE TABLE refgene_hg38
(
  bin integer NOT NULL,
  chr integer,
  trxrange int8range,
  cdsrange int8range,
  exoncount int,
  trxcount int,
  name2 character varying(255) COLLATE pg_catalog."C"
);

CREATE TABLE refgene_trx_hg38
(
  bin integer NOT NULL,
  name character varying(255) COLLATE pg_catalog."C",
  chr integer,
  strand character(1),
  trxrange int8range,
  cdsrange int8range,
  exoncount int,
  score bigint,
  name2 character varying(255) COLLATE pg_catalog."C",
  cdsstartstat character varying(255) COLLATE pg_catalog."C",
  cdsendstat character varying(255) COLLATE pg_catalog."C",
  
  -- We keep these field only for the import. We delete them at the end of this script
  trxstart bigint,
  trxend bigint,
  cdsstart bigint,
  cdsend bigint
);

CREATE TABLE refgene_exon_hg38
(
  bin integer NOT NULL,
  chr integer,
  exonpos int,
  exoncount int,
  exonrange int8range,
  
  -- We keep these field only for the import. We delete them at the end of this script
  i_exonstart character varying(255),
  i_exonend character varying(255),
  i_exonstarts character varying(10)[]
);






--
-- Migrate imported data to regovar database
--
INSERT INTO refgene_trx_hg38 (bin, name, chr, strand, trxrange, cdsrange, exoncount, score, name2, cdsstartstat, cdsendstat, trxstart, trxend, cdsstart, cdsend)
SELECT bin, name, 
  CASE WHEN chrom='chrX' THEN 23 WHEN chrom='chrY' THEN 24 WHEN chrom='chrM' THEN 25 ELSE CAST(substring(chrom from 4) AS INTEGER) END, 
  strand, int8range(trxstart, trxend), int8range(cdsstart, cdsend), exoncount, score, name2, cdsstartstat, cdsendstat, trxstart, trxend, cdsstart, cdsend
FROM import_refgene_hg38
WHERE char_length(chrom) <= 5;

INSERT INTO refgene_hg38 (bin, chr, trxrange, cdsrange, exoncount, trxcount, name2)
SELECT min(bin) AS bin, min(chr) AS chr, int8range(min(trxstart), max(trxend)) AS trxrange, int8range(min(cdsstart), max(cdsend)) AS cdsrange, max(exoncount) AS exoncount, count(*) AS trxcount, name2 
FROM refgene_trx_hg38 GROUP BY name2;

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
  
-- Remove useless columns
ALTER TABLE refgene_trx_hg38 DROP COLUMN trxstart;
ALTER TABLE refgene_trx_hg38 DROP COLUMN trxend;
ALTER TABLE refgene_trx_hg38 DROP COLUMN cdsstart;
ALTER TABLE refgene_trx_hg38 DROP COLUMN cdsend;
ALTER TABLE refgene_exon_hg38 DROP COLUMN i_exonstart;
ALTER TABLE refgene_exon_hg38 DROP COLUMN i_exonend;
ALTER TABLE refgene_exon_hg38 DROP COLUMN i_exonstarts;




--
-- Create indexes
--
CREATE INDEX refgene_hg38_chr_trxrange_idx
  ON refgene_hg38
  USING btree (chr, trxrange);


CREATE INDEX refgene_hg38_trxrange_idx
  ON refgene_hg38
  USING gist (trxrange);


CREATE INDEX refgene_trx_hg38_chr_trxrange_idx
  ON refgene_trx_hg38
  USING btree (chr, trxrange);


CREATE INDEX refgene_trx_hg38_trxrange_idx
  ON refgene_trx_hg38
  USING gist (trxrange);

  
CREATE INDEX refgene_exon_hg38_chr_exonange_idx
  ON refgene_exon_hg38
  USING btree (chr, exonrange);

  
CREATE INDEX refgene_exon_hg38_exonange_idx
  ON refgene_exon_hg38
  USING gist (exonrange);




--
-- Register refGen into regovar database
-- 

-- dbuid = md5 of refId, annotation db name and annotation db version
-- 4915f6f892d359e93ac0631fd1e76f7a = SELECT MD5(concat(3, 'refgene_hg38',      '2017-09-24 23:51'))
-- c721472eed11a0483ced649c0a53e37c = SELECT MD5(concat(3, 'refgene_trx_hg38',  '2017-09-24 23:51'))
INSERT INTO annotation_database(uid, reference_id, version, name, name_ui, description, url, ord, update_date, jointure, type) VALUES 
  ('4915f6f892d359e93ac0631fd1e76f7a', 3,
  '2017-09-24 23:51', 
  'refgene_hg38', 
  'refGene', 
  'Known human protein-coding and non-protein-coding genes taken from the NCBI RNA reference sequences collection (RefSeq).', 
  'http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz', 
  10, 
  CURRENT_TIMESTAMP, 
  'refgene_hg38 ON {0}.bin=refgene_hg38.bin AND {0}.chr=refgene_hg38.chr AND refgene_hg38.trxrange @> int8({0}.pos)',
  'site'),
  
  ('c721472eed11a0483ced649c0a53e37c', 3,
  '2017-09-24 23:51', 
  'refgene_trx_hg38', 
  'refGene Transcripts', 
  'Known human protein-coding and non-protein-coding transcripts taken from the NCBI RNA reference sequences collection (RefSeq).', 
  'http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz', 
  11, 
  CURRENT_TIMESTAMP, 
  'refgene_trx_hg38 ON {0}.bin=refgene_trx_hg38.bin AND {0}.chr=refgene_trx_hg38.chr AND refgene_trx_hg38.trxrange @> int8({0}.pos)',
  'site');




INSERT INTO annotation_field(database_uid, ord, name, name_ui, type, description, meta) VALUES
  ('4915f6f892d359e93ac0631fd1e76f7a', 6,  'trxrange',      'trxrange',     'range',  'Transcription region [start-end].', NULL),
  ('4915f6f892d359e93ac0631fd1e76f7a', 9,  'cdsrange',      'cdsrange',     'range',  'Coding region [start-end].', NULL),
  ('4915f6f892d359e93ac0631fd1e76f7a', 10, 'exoncount',     'exoncount',    'int',    'Number of exons in the gene.', NULL),
  ('4915f6f892d359e93ac0631fd1e76f7a', 10, 'trxcount',      'trxcount',     'int',    'Number of transcript in the gene.', NULL),
  ('4915f6f892d359e93ac0631fd1e76f7a', 12, 'name2',         'name2',        'string', 'Gene name.', NULL),
  
  ('c721472eed11a0483ced649c0a53e37c', 1,  'name',          'name',         'string', 'Transcript name.', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 3,  'strand',        'strand',       'string', 'Which DNA strand contains the observed alleles.', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 4,  'trxstart',      'trxstart',     'int',    'Transcription start position.', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 5,  'trxend',        'trxend',       'int',    'Transcription end position.', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 6,  'trxrange',      'trxrange',     'range',  'Transcription region [start-end].', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 7,  'cdsstart',      'cdsstart',     'int',    'Coding region start.', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 8,  'cdsend',        'cdsend',       'int',    'Coding region end.', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 9,  'cdsrange',      'cdsrange',     'range',  'Coding region [start-end].', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 10, 'exoncount',     'exoncount',    'int',    'Number of exons in the gene.', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 11, 'score',         'score',        'int',    'Score ?', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 12, 'name2',         'name2',        'string', 'Gene name.', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 13, 'cdsstartstat',  'cdsstartstat', 'string', 'Cds start stat, can be "non", "unk", "incompl" or "cmp1".', NULL),
  ('c721472eed11a0483ced649c0a53e37c', 14, 'cdsendstat',    'cdsendstat',   'string', 'Cds end stat, can be "non", "unk", "incompl" or "cmp1".', NULL);
  

UPDATE annotation_field SET uid=MD5(concat(database_uid, name));
DROP TABLE IF EXISTS import_refgene_hg38;

