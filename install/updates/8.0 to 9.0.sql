
DROP TABLE IF EXISTS hpo_phenotype;
DROP TABLE IF EXISTS hpo_disease;

-- Create new hpo table
CREATE TABLE hpo_phenotype
(
    hpo_id character varying(10) COLLATE pg_catalog."C",
    parent character varying(10) COLLATE pg_catalog."C" DEFAULT NULL,
    childs character varying(10)[] COLLATE pg_catalog."C" DEFAULT NULL,
    label text COLLATE pg_catalog."C",
    definition text COLLATE pg_catalog."C",
    search text COLLATE pg_catalog."C",
    genes text COLLATE pg_catalog."C" DEFAULT NULL,
    diseases text COLLATE pg_catalog."C" DEFAULT NULL,
    allsubs_genes text COLLATE pg_catalog."C" DEFAULT NULL,
    allsubs_diseases text COLLATE pg_catalog."C" DEFAULT NULL,
    allsubs_genes_count integer DEFAULT 0,
    allsubs_diseases_count integer DEFAULT 0,
    allsubs_count integer DEFAULT 0
);
CREATE TABLE hpo_disease
(
    hpo_id character varying(10) COLLATE pg_catalog."C",
    label text COLLATE pg_catalog."C",
    definition text COLLATE pg_catalog."C",
    search text COLLATE pg_catalog."C",
    genes character varying(10)[] COLLATE pg_catalog."C" DEFAULT NULL,
    phenotypes character varying(10)[] COLLATE pg_catalog."C" DEFAULT NULL
); 

CREATE INDEX hpo_term_idx 
    ON hpo_term 
    USING btree (hpo_id);

-- Create new phenotype table
CREATE TABLE public.subject_phenotype
(
    subject_id integer NOT NULL,
    hpo_id character varying(10) COLLATE pg_catalog."C" NOT NULL,
    added_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT sp_pkey PRIMARY KEY (subject_id, hpo_id)
);


-- Update database version
UPDATE parameter SET value='9.0' WHERE key='database_version';
INSERT INTO "event" (message, type) VALUES ('Update database to version 9.0', 'technical');