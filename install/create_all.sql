
-- 
-- CREATE ALL - V0.2.1
--





-- --------------------------------------------
-- FUNCTIONS
-- --------------------------------------------
-- Return array with element that occure in both input arrays
CREATE OR REPLACE FUNCTION array_intersect(anyarray, anyarray)
  RETURNS integer ARRAY
  LANGUAGE sql
AS $FUNCTION$
    SELECT ARRAY(
      SELECT UNNEST($1)
      INTERSECT
      SELECT UNNEST($2)
    );
$FUNCTION$;


-- Remove all occurence elements from an array into another one 
CREATE OR REPLACE FUNCTION array_multi_remove(integer[], integer[])
  RETURNS integer ARRAY
  LANGUAGE plpgsql
AS $FUNCTION$
  DECLARE
    source ALIAS FOR $1;
    to_remove ALIAS FOR $2;
  BEGIN
    FOR i IN array_lower(to_remove, 1)..array_upper(to_remove, 1) LOOP
      source := array_remove(source, to_remove[i]);
    END LOOP;
  RETURN source;
  END;
$FUNCTION$;


-- return index position (1-based) of an element into an array
CREATE OR REPLACE FUNCTION array_search(needle ANYELEMENT, haystack ANYARRAY)
RETURNS INT AS $$
    SELECT i
      FROM generate_subscripts($2, 1) AS i
     WHERE $2[i] = $1
  ORDER BY i
$$ LANGUAGE sql STABLE;



-- keep element in the first array if equivalent bool in the second array is true
CREATE OR REPLACE FUNCTION array_mask(anyarray, boolean[])
RETURNS anyarray AS $$ 
SELECT ARRAY(SELECT $1[i] 
  FROM generate_subscripts($1,1) g(i)
  WHERE $2[i])
$$ LANGUAGE sql;










-- --------------------------------------------
-- TYPES
-- --------------------------------------------
CREATE TYPE file_status AS ENUM ('uploading', 'uploaded', 'checked', 'error');
CREATE TYPE pipe_status AS ENUM ('initializing', 'installing', 'ready', 'error');
CREATE TYPE job_status AS ENUM ('waiting', 'initializing', 'running', 'pause', 'finalizing', 'done', 'canceled', 'error');
CREATE TYPE field_type AS ENUM ('int', 'string', 'float', 'enum', 'range', 'bool', 'sequence', 'list', 'sample_array');
CREATE TYPE annotation_db_type AS ENUM ('site', 'variant', 'transcript');
CREATE TYPE sample_status AS ENUM ('empty', 'loading', 'ready', 'error');
CREATE TYPE analysis_status AS ENUM ('empty', 'waiting', 'computing', 'ready', 'error');
CREATE TYPE event_type AS ENUM ('info', 'warning', 'error');
CREATE TYPE sex_type AS ENUM ('male', 'female', 'unknow');









-- --------------------------------------------
-- TABLES
-- --------------------------------------------
CREATE TABLE public.user
(
    id serial NOT NULL,
    login character varying(255) COLLATE pg_catalog."C" NOT NULL,
    password text COLLATE pg_catalog."C",
    email text COLLATE pg_catalog."C",
    firstname text COLLATE pg_catalog."C",
    lastname text COLLATE pg_catalog."C",
    function text COLLATE pg_catalog."C",
    location text COLLATE pg_catalog."C",
    settings json,
    roles json,
    is_activated boolean DEFAULT True,
    sandbox_id integer,
    create_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT user_pkey PRIMARY KEY (id),
    CONSTRAINT user_ukey1 UNIQUE (login),
    CONSTRAINT user_ukey2 UNIQUE (email)
);


CREATE TABLE public.project
(
    id serial NOT NULL,
    name character varying(255) COLLATE pg_catalog."C",
    comment text COLLATE pg_catalog."C",
    parent_id integer,
    is_folder boolean DEFAULT False,
    create_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_sandbox boolean DEFAULT False,
    CONSTRAINT project_pkey PRIMARY KEY (id)
);



CREATE TABLE subject
(
    id serial NOT NULL,
    identifier character varying(255) COLLATE pg_catalog."C",
    firstname text COLLATE pg_catalog."C",
    lastname text COLLATE pg_catalog."C",
    sex sex_type DEFAULT 'unknow',
    family_number text COLLATE pg_catalog."C",
    dateofbirth timestamp without time zone,
    dateofdeath timestamp without time zone,
    comment text COLLATE pg_catalog."C",
    create_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT subject_pkey PRIMARY KEY (id)
);



CREATE TABLE public.file
(
    id serial NOT NULL,
    name character varying(255) COLLATE pg_catalog."C",
    type character varying(10) COLLATE pg_catalog."C",
    comment text COLLATE pg_catalog."C",
    "path" text COLLATE pg_catalog."C",
    size bigint DEFAULT 0,
    upload_offset bigint DEFAULT 0,
    status file_status,
    create_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tags text COLLATE pg_catalog."C",
    md5sum character varying(32) COLLATE pg_catalog."C",
    job_source_id int,
    CONSTRAINT file_pkey PRIMARY KEY (id),
    CONSTRAINT file_ukey UNIQUE ("path")
);


CREATE TABLE public.pipeline
(
    id serial NOT NULL,
    name character varying(255) COLLATE pg_catalog."C",
    type character varying(50) COLLATE pg_catalog."C",
    status pipe_status,
    description text COLLATE pg_catalog."C",
    developers json,
    installation_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,

    version character varying(50) COLLATE pg_catalog."C",
    pirus_api character varying(50) COLLATE pg_catalog."C",

    image_file_id int,
    "path" text COLLATE pg_catalog."C",
    manifest json,
    documents json,
    starred boolean,
    CONSTRAINT pipe_pkey PRIMARY KEY (id)
);


CREATE TABLE public.job
(
    id serial NOT NULL,
    pipeline_id int,
    project_id int,
    name character varying(255) COLLATE pg_catalog."C",
    priority int,
    comment text COLLATE pg_catalog."C",

    config json,
    create_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status job_status,

    "path" text COLLATE pg_catalog."C",
    progress_value real,
    progress_label text COLLATE pg_catalog."C",

    CONSTRAINT job_pkey PRIMARY KEY (id)
);


CREATE TABLE public.job_file
(
    job_id int NOT NULL,
    file_id int NOT NULL,
    as_input boolean,
    CONSTRAINT job_file_pkey PRIMARY KEY (job_id, file_id)
);












CREATE TABLE public.template
(
    id serial NOT NULL,
    name character varying(255) COLLATE pg_catalog."C",
    description text COLLATE pg_catalog."C",
    version character varying(50) COLLATE pg_catalog."C",
    create_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    parent_id integer,
    configuration json,
    CONSTRAINT template_pkey PRIMARY KEY (id)
);





CREATE TABLE public.analysis
(
    id serial NOT NULL,
    project_id integer,
    name character varying(255) COLLATE pg_catalog."C",
    comment text COLLATE pg_catalog."C",
    settings json,
    fields json,
    filter json,
    "order" json,
    selection json,
    create_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_variants integer DEFAULT 0,
    statistics json,
    reference_id integer,
    computing_progress JSON,
    status analysis_status,
    CONSTRAINT analysis_pkey PRIMARY KEY (id)
);




CREATE TABLE public.filter
(
    id serial NOT NULL,
    analysis_id integer,
    name character varying(255) COLLATE pg_catalog."C",
    description text COLLATE pg_catalog."C",
    filter json,
    total_variants integer,
    total_results integer,
    progress real,
    CONSTRAINT filter_pkey PRIMARY KEY (id)
);













CREATE TABLE public."reference"
(
    id serial NOT NULL,
    name character varying(50) COLLATE pg_catalog."C",
    description text COLLATE pg_catalog."C",
    url text COLLATE pg_catalog."C",
    table_suffix character varying(10) COLLATE pg_catalog."C",
    CONSTRAINT reference_pkey PRIMARY KEY (id)
);









CREATE TABLE public.sample
(
    id serial NOT NULL,
    subject_id integer,
    name character varying(255) COLLATE pg_catalog."C",
    comment character varying(255) COLLATE pg_catalog."C",
    is_mosaic boolean,
    file_id integer,
    loading_progress real DEFAULT 0,
    reference_id integer,
    status sample_status,
    default_dbuid JSON,
    filter_description JSON,
    stats JSON,
    create_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT sample_pkey PRIMARY KEY (id)
);




CREATE TABLE public.analysis_sample
(
    analysis_id integer NOT NULL,
    sample_id integer NOT NULL,
    nickname character varying(255) COLLATE pg_catalog."C",
    CONSTRAINT analysis_sample_pkey PRIMARY KEY (analysis_id, sample_id)
);


CREATE TABLE public.attribute
(
    analysis_id integer NOT NULL,
    sample_id integer NOT NULL,
    name character varying(255) COLLATE pg_catalog."C" NOT NULL,
    value character varying(255) COLLATE pg_catalog."C",
    wt_col_id character varying(32) COLLATE pg_catalog."C",
    CONSTRAINT attribute_pkey PRIMARY KEY (analysis_id, sample_id, name)
);





CREATE TABLE public.annotation_database
(
    uid character varying(32) COLLATE pg_catalog."C",
    reference_id integer NOT NULL,
    name character varying(255) COLLATE pg_catalog."C" NOT NULL,
    version character varying(255) COLLATE pg_catalog."C" NOT NULL,
    name_ui character varying(255) COLLATE pg_catalog."C",
    description text,
    type annotation_db_type,
    ord integer,
    url text ,
    update_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    jointure text,
    db_pk_field_uid character varying(32) COLLATE pg_catalog."C",
    CONSTRAINT annotation_database_pkey PRIMARY KEY (uid)
);


CREATE TABLE public.annotation_field
(
    uid character varying(32) COLLATE pg_catalog."C",
    database_uid character varying(32) COLLATE pg_catalog."C" NOT NULL,
    name character varying(255) COLLATE pg_catalog."C" NOT NULL,
    name_ui character varying(255) COLLATE pg_catalog."C",
    ord integer,
    description text,
    type field_type,
    meta json,
    CONSTRAINT annotation_field_pkey PRIMARY KEY (database_uid, name)
);





CREATE TABLE public."parameter"
(
    key character varying(255) COLLATE pg_catalog."C" NOT NULL ,
    value character varying(255) COLLATE pg_catalog."C" NOT NULL,
    description character varying(255) COLLATE pg_catalog."C",
    CONSTRAINT parameter_pkey PRIMARY KEY (key)
);





CREATE TABLE public.event
(
    id bigserial NOT NULL,
    "date" timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message text COLLATE pg_catalog."C",
    type event_type,
    meta JSON,
    CONSTRAINT event_pkey PRIMARY KEY (id)
);





/*
CREATE TABLE public.project_subject
(
    project_id integer NOT NULL,
    subject_id integer NOT NULL,
    CONSTRAINT ps_pkey PRIMARY KEY (project_id, subject_id)
);

CREATE TABLE public.project_file
(
    project_id integer NOT NULL,
    file_id integer NOT NULL,
    CONSTRAINT pf_pkey PRIMARY KEY (project_id, file_id)
);*/

CREATE TABLE public.subject_file
(
    subject_id integer NOT NULL,
    file_id integer NOT NULL,
    CONSTRAINT sf_pkey PRIMARY KEY (subject_id, file_id)
);

CREATE TABLE public.analysis_file
(
    analysis_id integer NOT NULL,
    file_id integer NOT NULL,
    CONSTRAINT analysis_file_pkey PRIMARY KEY (analysis_id, file_id)
);






CREATE TABLE public.indicator
(
    id serial NOT NULL,
    name text COLLATE pg_catalog."C" NOT NULL,
    description text COLLATE pg_catalog."C",
    meta JSON,
    CONSTRAINT indicator_pkey PRIMARY KEY (id)
);
CREATE TABLE public.subject_indicator_value
(
    subject_id integer NOT NULL,
    indicator_id integer NOT NULL,
    value character varying(50) COLLATE pg_catalog."C",
    CONSTRAINT siv_pkey PRIMARY KEY (subject_id, indicator_id)
);
CREATE TABLE public.analysis_indicator_value
(
    analysis_id integer NOT NULL,
    indicator_id integer NOT NULL,
    value character varying(50) COLLATE pg_catalog."C",
    CONSTRAINT aiv_pkey PRIMARY KEY (analysis_id, indicator_id)
);
CREATE TABLE public.job_indicator_value
(
    job_id integer NOT NULL,
    indicator_id integer NOT NULL,
    value character varying(50) COLLATE pg_catalog."C",
    CONSTRAINT jiv_pkey PRIMARY KEY (job_id, indicator_id)
);




CREATE TABLE public.panel
(
    id character varying(50) COLLATE pg_catalog."C",
    name text COLLATE pg_catalog."C",
    description text COLLATE pg_catalog."C",
    owner text COLLATE pg_catalog."C",
    create_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    shared boolean DEFAULT False,
    CONSTRAINT panel_pkey PRIMARY KEY (id)
);
CREATE TABLE public.panel_entry
(
    id character varying(50) COLLATE pg_catalog."C" NOT NULL,
    panel_id character varying(50) COLLATE pg_catalog."C" NOT NULL,
    version character varying(50) COLLATE pg_catalog."C",
    comment text COLLATE pg_catalog."C",
    data JSON NOT NULL,
    create_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT panel_entry_pkey PRIMARY KEY (panel_id, version)
);






-- --------------------------------------------
-- SHARING SERVER TABLES
-- --------------------------------------------


-- panels shared
-- variants stats
-- regovar db's id/location
-- pipelines shared








-- --------------------------------------------
-- INDEXES
-- --------------------------------------------
CREATE INDEX sample_idx
  ON public.sample
  USING btree
  (id);


CREATE INDEX attribute_idx
  ON public.attribute
  USING btree
  (analysis_id, sample_id, name COLLATE pg_catalog."default");

CREATE INDEX analysis_idx
  ON public.analysis
  USING btree
  (id);


CREATE INDEX filter_idx
  ON public.filter
  USING btree
  (id);
    

CREATE INDEX annotation_database_idx
  ON public.annotation_database
  USING btree
  (reference_id, name, version);
CREATE INDEX annotation_database_idx2
  ON public.annotation_database
  USING btree (uid);


CREATE INDEX annotation_field_idx
  ON public.annotation_field
  USING btree
  (database_uid, name);
CREATE INDEX annotation_field_idx2
  ON public.annotation_field
  USING btree (uid);
  
  
CREATE INDEX subject_indicator_idx
  ON public.subject_indicator_value
  USING btree
  (subject_id, indicator_id);
CREATE INDEX analysis_indicator_idx
  ON public.analysis_indicator_value
  USING btree
  (analysis_id, indicator_id);
CREATE INDEX job_indicator_idx
  ON public.job_indicator_value
  USING btree
  (job_id, indicator_id);


CREATE INDEX panel_entry_idx
  ON public.panel_entry
  USING btree
  (panel_id, version);
  
  






-- --------------------------------------------
-- TABLES ACCORDING TO REF
-- --------------------------------------------
CREATE TABLE public.variant_hg18
(
    id bigserial NOT NULL,
    bin integer,
    chr integer,
    pos bigint NOT NULL,
    ref text NOT NULL,
    alt text NOT NULL,
    is_transition boolean,
    sample_list integer[],
    CONSTRAINT variant_hg18_pkey PRIMARY KEY (id),
    CONSTRAINT variant_hg18_ukey UNIQUE (chr, pos, ref, alt)
);
CREATE TABLE public.sample_variant_hg18
(
    sample_id integer NOT NULL,
    bin integer,
    chr integer,
    pos bigint NOT NULL,
    ref text NOT NULL,
    alt text NOT NULL,
    variant_id bigint,
    genotype integer,
    depth integer,
    infos character varying(255)[][] COLLATE pg_catalog."C",
    mosaic real,
    CONSTRAINT sample_variant_hg18_pkey PRIMARY KEY (sample_id, chr, pos, ref, alt),
    CONSTRAINT sample_variant_hg18_ukey UNIQUE (sample_id, variant_id)
);
CREATE INDEX sample_variant_hg18_idx_id
  ON public.sample_variant_hg18
  USING btree
  (variant_id);
CREATE INDEX sample_variant_hg18_idx_samplevar
  ON public.sample_variant_hg18
  USING btree
  (sample_id);
CREATE INDEX sample_variant_hg18_idx_site
  ON public.sample_variant_hg18
  USING btree
  (sample_id, bin, chr, pos);
CREATE INDEX variant_hg18_idx_id
  ON public.variant_hg18
  USING btree
  (id);
CREATE INDEX variant_hg18_idx_site
  ON public.variant_hg18
  USING btree
  (bin, chr, pos);



  
























-- --------------------------------------------
-- INIT DATA
-- --------------------------------------------
INSERT INTO public."parameter" (key, description, value) VALUES
    ('database_version',          'The current version of the database',           '0.6.5'),
    ('backup_date',               'The date of the last database dump',            to_char(current_timestamp, 'YYYY-MM-DD')),
    ('stats_refresh_date',        'The date of the last refresh of statistics',    to_char(current_timestamp, 'YYYY-MM-DD'));





-- 2c0a7043a9e736eaf14b6614fff102c0 = SELECT MD5('Regovar')
-- 492f18b60811bf85ce118c0c6a1a5c4a = SELECT MD5('Variant')
INSERT INTO public.annotation_database(uid, reference_id, name, version, name_ui, description, url, ord,  jointure, type) VALUES
  ('492f18b60811bf85ce118c0c6a1a5c4a', 0, 'wt', '_all_', 'Variant', 'Basic information about the variant.', '',  0, '', 'variant'),
  ('2c0a7043a9e736eaf14b6614fff102c0', 0, 'wt', '_all_', 'Regovar', 'Regovar computed annotations'        , '',  1, '', 'variant');

INSERT INTO public.annotation_field(database_uid, ord, name, name_ui, type, description, meta) VALUES
  ('492f18b60811bf85ce118c0c6a1a5c4a', 1,  'variant_id',       'id',                     'int',          'Variant unique ID in the database.', NULL),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 2,  'vcf_line',         'vcf line',               'int',          'Corresponding line in the VCF file.', NULL),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 3,  'chr',              'chr',                    'int',          'Chromosome as number : 23=X, 24=Y, 25=M.', NULL),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 4,  'pos',              'pos',                    'int',          'Position of the variant in the chromosome.', NULL),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 5,  'ref',              'ref',                    'sequence',     'Reference sequence.', NULL),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 6,  'alt',              'alt',                    'sequence',     'Alternative sequence of the variant.', NULL),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 10, 's{}_gt',           'GT',                     'sample_array', 'Genotype as number : 0="r/r", 1="a/a", 2="r/a", 3="a1/a2".', '{"type": "int"}'),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 11, 's{}_dp',           'DP',                     'sample_array', 'Depth.', '{"type": "int"}'),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 12, 's{}_dp_alt',       'DP alt',                 'sample_array', 'Allelic depth.', '{"type": "int"}'),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 13, 's{}_qual',         'QUAL',                   'sample_array', 'VCF Quality field.', '{"type": "float"}'),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 14, 's{}_filter',       'FILTER',                 'sample_array', 'VCF Filter field', '{"type": "enum"}'),
  ('492f18b60811bf85ce118c0c6a1a5c4a', 50, 'regovar_score',    'Regovar Pred',           'enum',         'Regovar users annotation.', '{"type": "enum", "values": ["Artifact", "Yes", "No"]}');

INSERT INTO public.annotation_field(database_uid, ord, name, name_ui, type, description, meta) VALUES
  ('2c0a7043a9e736eaf14b6614fff102c0', 0,  'is_selected',      'Selected',                       'bool',         'Is the variant in the user selection or not.', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 1,  'is_dom',           'Dominant',                       'bool',         'Is the variant dominant for the sample (single), or for the child (trio).', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 2,  'is_rec_hom',       'Recessif homozygous',            'bool',         'Is the variant recessif homozygous for the sample (single), or for the child (trio).', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 3,  'is_rec_htzcomp',   'Recessif compound heterozygous', 'bool',         'Is the variant recessif compound heterozygous for the sample (single), or for the child (trio).', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 4,  'is_denovo',        'De novo',                        'bool',         'Is the variant de novo for the child (trio). The remaining "de novo" variants also include uncovered locus in the parents.', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 6,  'is_aut',           'Autosomal',                      'bool',         'Is the variant autosomal for the sample (single), or for the child (trio).', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 7,  'is_xlk',           'X-linked',                       'bool',         'Is the variant X-linked for the sample (single), or for the child (trio).', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 8,  'is_mit',           'Mitochondrial',                  'bool',         'Is the variant mitochondrial for the sample (single), or for the child (trio).', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 10, 'sample_tlist',     'samples total',                  'string',       'List of sample in the whole database that have the variant.', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 11, 'sample_tcount',    'samples total count',            'int',          'Number of sample in the whole database that have the variant.', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 12, 'sample_alist',     'samples analysis',               'string',       'List of sample in the analysis that have the variant.', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 13, 'sample_acount',    'samples analysis count',         'int',          'Number of sample in the analysis that have the variant.', NULL),
  ('2c0a7043a9e736eaf14b6614fff102c0', 14, 's{}_is_composite', 'is composite',                   'sample_array', 'Is the variant composite for this sample.', '{"type": "bool"}');

UPDATE annotation_field SET uid=MD5(concat(database_uid, name));



INSERT INTO "indicator" (name, meta) VALUES
  ('Ermergency', '{"enum" : ["Burning", "Urgent", "Normal", "Low"], "default": "Normal"}');

INSERT INTO "project" (id, name, comment) VALUES  
  (0, 'Trash', 'Special project that contains all analyses that have been deleted by non admin users');
INSERT INTO "project" (comment, is_sandbox) VALUES
  ('My sandbox', True);
INSERT INTO "user" (login, firstname, lastname, roles, sandbox_id) VALUES
  ('admin', 'Root', 'Administrator', '{"Administration": "Write"}', 1);



INSERT INTO "event" (message, type) VALUES
  ('Regovar database creation', 'info'),
  ('Default root admin user created', 'info');
  
  

