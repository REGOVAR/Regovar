
--
-- Fake reference
--
INSERT INTO reference(id, name, table_suffix) VALUES (1, 'Hg19', 'hg19');
CREATE TABLE variant_hg19
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
    CONSTRAINT variant_hg19_pkey PRIMARY KEY (id),
    CONSTRAINT variant_hg19_ukey UNIQUE (chr, pos, ref, alt)
);
CREATE TABLE sample_variant_hg19
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
    CONSTRAINT sample_variant_hg19_pkey PRIMARY KEY (sample_id, chr, pos, ref, alt),
    CONSTRAINT sample_variant_hg19_ukey UNIQUE (sample_id, variant_id)
);
CREATE TABLE refgene_hg19
(
  bin integer NOT NULL,
  chr integer,
  txrange int8range,
  cdsrange int8range,
  exoncount int,
  trxcount int,
  name2 character varying(255) COLLATE pg_catalog."C"
);
CREATE TABLE refgene_trx_hg19
(
  bin integer NOT NULL,
  name character varying(255) COLLATE pg_catalog."C",
  chr integer,
  strand character(1),
  txrange int8range,
  cdsrange int8range,
  exoncount int,
  score bigint,
  name2 character varying(255) COLLATE pg_catalog."C",
  cdsstartstat character varying(255) COLLATE pg_catalog."C",
  cdsendstat character varying(255) COLLATE pg_catalog."C"
);
CREATE INDEX sample_variant_hg19_idx_id
  ON sample_variant_hg19
  USING btree
  (variant_id);
CREATE INDEX sample_variant_hg19_idx_samplevar
  ON sample_variant_hg19
  USING btree
  (sample_id);
CREATE INDEX sample_variant_hg19_idx_site
  ON sample_variant_hg19
  USING btree
  (sample_id, bin, chr, pos);
CREATE INDEX variant_hg19_idx_id
  ON variant_hg19
  USING btree
  (id);
CREATE INDEX variant_hg19_idx_site
  ON variant_hg19
  USING btree
  (bin, chr, pos);






--
-- Fake users
--
INSERT INTO "user" (login, email, firstname, lastname, function, location, settings, roles, is_activated, sandbox_id) VALUES
    -- WARNING, Admin user added by default, so, id=1 is already created
    ('U2', 'user2@email.com', 'firstname2', 'lastname2', 'f2', 'l2', '{"fullscreen": true}', '{"Administration": "Read"}', True, 2),
    ('U3', 'user3@email.com', 'firstname3', 'lastname3', 'f3', 'l3', '{"fullscreen": true}', '{}',                         True, 3),
    ('U4', 'user4@email.com', 'firstname4', 'lastname4', 'f4', 'l4', NULL,                   '{}',                         False,4);

INSERT INTO project (name, comment, parent_id, is_folder, is_sandbox) VALUES
     -- WARNING, Admin user added by default, so, id=1 is already created for the sandbox project of the admin
    ('sandbox U2', 'comment', NULL, False, True),
    ('sandbox U3', 'comment', NULL, False, True),
    ('sandbox U4', 'comment', NULL, False, True);

    


--
-- Fake projects
--
INSERT INTO project (name, comment, parent_id, is_folder, is_sandbox) VALUES
    ('folder',     'comment', NULL, True,  False),
    ('P1',         'comment', 5,    False, False),
    ('P2',         'comment', NULL, False, False);





--
-- Fake subjects and samples
--
INSERT INTO subject (identifier, firstname, lastname, sex) VALUES
    ('S1', 'firstname1', 'lastname1', 'male'),
    ('S2', 'firstname2', 'lastname2', 'female');
    
INSERT INTO sample (subject_id, name, is_mosaic, file_id, loading_progress, reference_id, status) VALUES
    (1,    'sp_1', False, 3, 1, 1, 'ready'),
    (1,    'sp_2', False, 4, 1, 1, 'ready'),
    (NULL, 'sp_3', True,  1, 1, 1, 'ready');

    
    
INSERT INTO subject_indicator_value (subject_id, indicator_id, value) VALUES
    (1, 1, 'Urgent'),
    (2, 1, 'Low');






--
-- TEST FILE PIPELINE AND JOB
--
INSERT INTO file (name, type, size, upload_offset, status, job_source_id) VALUES
    ('F1.tar.xz', 'tar.xz', 30000,  30000,  'uploaded',  NULL),
    ('F2.tar.xz', 'tar.xz', 30000,  20000,  'uploading', NULL),
    ('F3.bin',    'bin',    100000, 100000, 'checked',   NULL),
    ('F4.vcf',    'vcf',    100000, 100000, 'checked',   1);

INSERT INTO pipeline (name, type, status, description, developers, image_file_id, manifest, documents) VALUES
    ('P1', 'github', 'ready',      'description', '["ikit", "dridk"]', 1, '{}', '[]'),
    ('P2', 'lxd',    'installing', 'description', '["oodnadata"]',     2, NULL, NULL);

INSERT INTO job (pipeline_id, project_id, name, config, status, progress_value, progress_label) VALUES
    (1, 6, 'J1', '{}', 'done',  1,   '100%'),
    (1, 6, 'J2', '{}', 'pause', 0.5, 'Step : 4/8');

INSERT INTO job_file (job_id, file_id, as_input) VALUES
    (1, 3, True),
    (1, 4, False);
    





--
-- TEST ANALYSIS (SAMPLE, ATTRIBUTES, FILTER, ...)
--


  
  
        
--
-- TEST EVENTS (with PROJECT, USER, SUBJECT, JOB, ANALYSIS, FILE)
--


        
--
-- TEST PANEL
--

















