
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
CREATE TYPE analysis_status AS ENUM ('empty', 'computing', 'ready', 'error');
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
    identifiant character varying(255) COLLATE pg_catalog."C",
    firstname text COLLATE pg_catalog."C",
    lastname text COLLATE pg_catalog."C",
    sex sex_type DEFAULT 'unknow',
    birthday timestamp without time zone,
    deathday timestamp without time zone,
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
    template_id integer,
    fields json,
    filter json,
    "order" json,
    selection json,
    create_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_variants integer DEFAULT 0,
    reference_id integer DEFAULT 2,  -- 2 is for Hg19
    computing_progress real DEFAULT 0,
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
    CONSTRAINT annotation_database_pkey PRIMARY KEY (reference_id, name, version)
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
    wt_default boolean DEFAULT False,
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

    user_id integer,
    project_id integer,
    analysis_id integer,
    file_id integer,
    subject_id integer,
    job_id integer,
    pipeline_id integer,
    CONSTRAINT event_pkey PRIMARY KEY (id)
);






CREATE TABLE public.project_subject
(
    project_id integer NOT NULL,
    subject_id integer NOT NULL,
    CONSTRAINT ps_pkey PRIMARY KEY (project_id, subject_id)
);



CREATE TABLE public.user_project_sharing
(
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    write_authorisation boolean,
    CONSTRAINT ups_pkey PRIMARY KEY (project_id, user_id)
);

CREATE TABLE public.user_subject_sharing
(
    subject_id integer NOT NULL,
    user_id integer NOT NULL,
    write_authorisation boolean,
    CONSTRAINT uss_pkey PRIMARY KEY (subject_id, user_id)
);

CREATE TABLE public.project_file
(
    project_id integer NOT NULL,
    file_id integer NOT NULL,
    CONSTRAINT pf_pkey PRIMARY KEY (project_id, file_id)
);

CREATE TABLE public.subject_file
(
    subject_id integer NOT NULL,
    file_id integer NOT NULL,
    CONSTRAINT sf_pkey PRIMARY KEY (subject_id, file_id)
);



CREATE TABLE public.indicator
(
    id serial NOT NULL,
    name text COLLATE pg_catalog."C" NOT NULL,
    description text COLLATE pg_catalog."C",
    default_value_id integer,
    CONSTRAINT indicator_pkey PRIMARY KEY (id)
);
CREATE TABLE public.indicator_value
(
    id serial NOT NULL,
    indicator_id integer NOT NULL,
    name text COLLATE pg_catalog."C" NOT NULL,
    description text COLLATE pg_catalog."C",
    style json,
    CONSTRAINT iv_pkey PRIMARY KEY (id)
);
CREATE TABLE public.project_indicator
(
    indicator_id integer NOT NULL,
    project_id integer,
    indicator_value_id integer NOT NULL,
    CONSTRAINT pi_pkey PRIMARY KEY (indicator_id, project_id)
);
CREATE TABLE public.subject_indicator
(
    indicator_id integer NOT NULL,
    subject_id integer,
    indicator_value_id integer NOT NULL,
    CONSTRAINT si_pkey PRIMARY KEY (indicator_id, subject_id)
);









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
  
  
  
  
  








-- --------------------------------------------
-- TABLES ACCORDING TO REF
-- --------------------------------------------
CREATE TABLE public.variant_hg19
(
    id bigserial NOT NULL,
    bin integer,
    chr integer,
    pos bigint NOT NULL,
    ref text NOT NULL,
    alt text NOT NULL,
    is_transition boolean,
    sample_list integer[],
    CONSTRAINT variant_hg19_pkey PRIMARY KEY (id),
    CONSTRAINT variant_hg19_ukey UNIQUE (chr, pos, ref, alt)
);
CREATE TABLE public.sample_variant_hg19
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
    is_composite boolean DEFAULT False,
    CONSTRAINT sample_variant_hg19_pkey PRIMARY KEY (sample_id, chr, pos, ref, alt),
    CONSTRAINT sample_variant_hg19_ukey UNIQUE (sample_id, variant_id)
);
CREATE INDEX sample_variant_hg19_idx_id
  ON public.sample_variant_hg19
  USING btree
  (variant_id);
CREATE INDEX sample_variant_hg19_idx_samplevar
  ON public.sample_variant_hg19
  USING btree
  (sample_id);
CREATE INDEX sample_variant_hg19_idx_site
  ON public.sample_variant_hg19
  USING btree
  (sample_id, bin, chr, pos);
CREATE INDEX variant_hg19_idx_id
  ON public.variant_hg19
  USING btree
  (id);
CREATE INDEX variant_hg19_idx_site
  ON public.variant_hg19
  USING btree
  (bin, chr, pos);




  
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



  
CREATE TABLE public.variant_hg38
(
    id bigserial NOT NULL,
    bin integer,
    chr integer,
    pos bigint NOT NULL,
    ref text NOT NULL,
    alt text NOT NULL,
    is_transition boolean,
    sample_list integer[],
    CONSTRAINT variant_hg38_pkey PRIMARY KEY (id),
    CONSTRAINT variant_hg38_ukey UNIQUE (chr, pos, ref, alt)
);
CREATE TABLE public.sample_variant_hg38
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
    CONSTRAINT sample_variant_hg38_pkey PRIMARY KEY (sample_id, chr, pos, ref, alt),
    CONSTRAINT sample_variant_hg38_ukey UNIQUE (sample_id, variant_id)
);
CREATE INDEX sample_variant_hg38_idx_id
  ON public.sample_variant_hg38
  USING btree
  (variant_id);
CREATE INDEX sample_variant_hg38_idx_samplevar
  ON public.sample_variant_hg38
  USING btree
  (sample_id);
CREATE INDEX sample_variant_hg38_idx_site
  ON public.sample_variant_hg38
  USING btree
  (sample_id, bin, chr, pos);
CREATE INDEX variant_hg38_idx_id
  ON public.variant_hg38
  USING btree
  (id);
CREATE INDEX variant_hg38_idx_site
  ON public.variant_hg38
  USING btree
  (bin, chr, pos);























-- --------------------------------------------
-- INIT DATA
-- --------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";



INSERT INTO public.reference(id, name, description, url, table_suffix) VALUES 
  (1, 'Hg18', 'Human Genom version 18', 'http://hgdownload.cse.ucsc.edu/goldenpath/hg18/chromosomes/', 'hg18'),
  (2, 'Hg19', 'Human Genom version 19', 'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/chromosomes/', 'hg19'),
  (3, 'Hg38', 'Human Genom version 38', 'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/chromosomes/', 'hg38');



CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
INSERT INTO public."parameter" (key, description, value) VALUES
    ('database_version',          'The current version of the database',           'V1.0.0'),
    ('heavy_client_last_version', 'Oldest complient version of the heavy client',  'V1.0.0'),
    ('backup_date',               'The date of the last database dump',            to_char(current_timestamp, 'YYYY-MM-DD')),
    ('stats_refresh_date',        'The date of the last refresh of statistics',    to_char(current_timestamp, 'YYYY-MM-DD'));






-- 8beee586e1cd098bc64b48403ed7755d = SELECT MD5(concat(reference_id=1, name='Variant', version=NULL))
-- d9121852fc1a279b95cb7e18c976f112 = SELECT MD5(concat(reference_id=2, name='Variant', version=NULL))
-- 7363e34fee56d2cb43583f9bd19d3980 = SELECT MD5(concat(reference_id=3, name='Variant', version=NULL))
INSERT INTO public.annotation_database(uid, reference_id, name, version, name_ui, description, url, ord,  jointure, type) VALUES
  ('8beee586e1cd098bc64b48403ed7755d', 1, 'sample_variant_hg18', '', 'Variant', 'Basic information about the variant.', '',  0, 'sample_variant_hg18', 'variant'),
  ('d9121852fc1a279b95cb7e18c976f112', 2, 'sample_variant_hg19', '', 'Variant', 'Basic information about the variant.', '',  0, 'sample_variant_hg19', 'variant'),
  ('7363e34fee56d2cb43583f9bd19d3980', 3, 'sample_variant_hg38', '', 'Variant', 'Basic information about the variant.', '',  0, 'sample_variant_hg38', 'variant');


INSERT INTO public.annotation_field(database_uid, ord, wt_default, name, name_ui, type, description, meta) VALUES
  ('8beee586e1cd098bc64b48403ed7755d', 1,  True, 'variant_id',       'id',                     'int',          'Variant unique id in the database.', NULL),
  ('8beee586e1cd098bc64b48403ed7755d', 3,  True, 'chr',              'chr',                    'enum',         'Chromosome.', '{"enum": {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", "10": "10", "11": "11", "12": "12", "13": "13", "14": "14", "15": "15", "16": "16", "17": "17", "18": "18", "19": "19", "20": "20", "21": "21", "22": "22", "23": "X", "24": "Y", "25": "M"}}'),
  ('8beee586e1cd098bc64b48403ed7755d', 4,  True, 'pos',              'pos',                    'int',          'Position of the variant in the chromosome.', NULL),
  ('8beee586e1cd098bc64b48403ed7755d', 5,  True, 'ref',              'ref',                    'sequence',     'Reference sequence.', NULL),
  ('8beee586e1cd098bc64b48403ed7755d', 6,  True, 'alt',              'alt',                    'sequence',     'Alternative sequence of the variant.', NULL),
  ('8beee586e1cd098bc64b48403ed7755d', 7,  True, 'sample_tlist',     'samples total',          'string',       'List of sample in the whole database that have the variant.', NULL),
  ('8beee586e1cd098bc64b48403ed7755d', 8,  True, 'sample_tcount',    'samples total count',    'int',          'Number of sample in the whole database that have the variant.', NULL),
  ('8beee586e1cd098bc64b48403ed7755d', 9,  True, 'sample_alist',     'samples analysis',       'string',       'List of sample in the analysis that have the variant.', NULL),
  ('8beee586e1cd098bc64b48403ed7755d', 10, True, 'sample_acount',    'samples analysis count', 'int',          'Number of sample in the analysis that have the variant.', NULL),
  ('8beee586e1cd098bc64b48403ed7755d', 20, True, 's{}_gt',           'GT',                     'sample_array', 'Genotype.', '{"type": "enum", "enum" : ["r/r", "a/a", "r/a", "a1/a2"]}'),
  ('8beee586e1cd098bc64b48403ed7755d', 30, True, 's{}_dp',           'DP',                     'sample_array', 'Depth.', '{"type": "int"}'),
  ('8beee586e1cd098bc64b48403ed7755d', 40, True, 's{}_is_composite', 'is composite',           'sample_array', 'Is the variant composite for this sample.', '{"type": "bool"}');

INSERT INTO public.annotation_field(database_uid, ord, wt_default, name, name_ui, type, description, meta) VALUES
  ('d9121852fc1a279b95cb7e18c976f112', 1,  True, 'variant_id',       'id',                     'int',          'Variant unique id in the database.', NULL),
  ('d9121852fc1a279b95cb7e18c976f112', 3,  True, 'chr',              'chr',                    'enum',         'Chromosome.', '{"enum": {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", "10": "10", "11": "11", "12": "12", "13": "13", "14": "14", "15": "15", "16": "16", "17": "17", "18": "18", "19": "19", "20": "20", "21": "21", "22": "22", "23": "X", "24": "Y", "25": "M"}}'),
  ('d9121852fc1a279b95cb7e18c976f112', 4,  True, 'pos',              'pos',                    'int',          'Position of the variant in the chromosome.', NULL),
  ('d9121852fc1a279b95cb7e18c976f112', 5,  True, 'ref',              'ref',                    'sequence',     'Reference sequence.', NULL),
  ('d9121852fc1a279b95cb7e18c976f112', 6,  True, 'alt',              'alt',                    'sequence',     'Alternative sequence of the variant.', NULL),
  ('d9121852fc1a279b95cb7e18c976f112', 7,  True, 'sample_tlist',     'samples total',          'string',       'List of sample in the whole database that have the variant.', NULL),
  ('d9121852fc1a279b95cb7e18c976f112', 8,  True, 'sample_tcount',    'samples total count',    'int',          'Number of sample in the whole database that have the variant.', NULL),
  ('d9121852fc1a279b95cb7e18c976f112', 9,  True, 'sample_alist',     'samples analysis',       'string',       'List of sample in the analysis that have the variant.', NULL),
  ('d9121852fc1a279b95cb7e18c976f112', 10, True, 'sample_acount',    'samples analysis count', 'int',          'Number of sample in the analysis that have the variant.', NULL),
  ('d9121852fc1a279b95cb7e18c976f112', 20, True, 's{}_gt',           'GT',                     'sample_array', 'Genotype.', '{"type": "enum", "enum" : ["r/r", "a/a", "r/a", "a1/a2"]}'),
  ('d9121852fc1a279b95cb7e18c976f112', 30, True, 's{}_dp',           'DP',                     'sample_array', 'Depth.', '{"type": "int"}'),
  ('d9121852fc1a279b95cb7e18c976f112', 40, True, 's{}_is_composite', 'is composite',           'sample_array', 'Is the variant composite for this sample.', '{"type": "bool"}');

INSERT INTO public.annotation_field(database_uid, ord, wt_default, name, name_ui, type, description, meta) VALUES
  ('7363e34fee56d2cb43583f9bd19d3980', 1,  True, 'variant_id',       'id',                     'int',          'Variant unique id in the database.', NULL),
  ('7363e34fee56d2cb43583f9bd19d3980', 3,  True, 'chr',              'chr',                    'enum',         'Chromosome.', '{"enum": {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", "10": "10", "11": "11", "12": "12", "13": "13", "14": "14", "15": "15", "16": "16", "17": "17", "18": "18", "19": "19", "20": "20", "21": "21", "22": "22", "23": "X", "24": "Y", "25": "M"}}'),
  ('7363e34fee56d2cb43583f9bd19d3980', 4,  True, 'pos',              'pos',                    'int',          'Position of the variant in the chromosome.', NULL),
  ('7363e34fee56d2cb43583f9bd19d3980', 5,  True, 'ref',              'ref',                    'sequence',     'Reference sequence.', NULL),
  ('7363e34fee56d2cb43583f9bd19d3980', 6,  True, 'alt',              'alt',                    'sequence',     'Alternative sequence of the variant.', NULL),
  ('7363e34fee56d2cb43583f9bd19d3980', 7,  True, 'sample_tlist',     'samples total',          'string',       'List of sample in the whole database that have the variant.', NULL),
  ('7363e34fee56d2cb43583f9bd19d3980', 8,  True, 'sample_tcount',    'samples total count',    'int',          'Number of sample in the whole database that have the variant.', NULL),
  ('7363e34fee56d2cb43583f9bd19d3980', 9,  True, 'sample_alist',     'samples analysis',       'string',       'List of sample in the analysis that have the variant.', NULL),
  ('7363e34fee56d2cb43583f9bd19d3980', 10, True, 'sample_acount',    'samples analysis count', 'int',          'Number of sample in the analysis that have the variant.', NULL),
  ('7363e34fee56d2cb43583f9bd19d3980', 20, True, 's{}_gt',           'GT',                     'sample_array', 'Genotype.', '{"type": "enum", "enum" : ["r/r", "a/a", "r/a", "a1/a2"]}'),
  ('7363e34fee56d2cb43583f9bd19d3980', 30, True, 's{}_dp',           'DP',                     'sample_array', 'Depth.', '{"type": "int"}'),
  ('7363e34fee56d2cb43583f9bd19d3980', 40, True, 's{}_is_composite', 'is composite',           'sample_array', 'Is the variant composite for this sample.', '{"type": "bool"}');

UPDATE annotation_field SET uid=MD5(concat(database_uid, name));



INSERT INTO "indicator" (name) VALUES
  ('Project basic status');
INSERT INTO "indicator_value" (indicator_id, name) VALUES
  (1, 'Open'),
  (1, 'Idle'),
  (1, 'Close');
  
INSERT INTO "project" (comment, is_sandbox) VALUES
  ('My sandbox', True);
INSERT INTO "user" (login, firstname, lastname, roles, sandbox_id) VALUES
  ('admin', 'Root', 'Administrator', '{"Administration": "Write"}', 1);



INSERT INTO "event" (message, type) VALUES
  ('Regovar database creation', 'info'),
  ('Default root admin user created', 'info');
  
  

