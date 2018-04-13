
CREATE TYPE phenotype_category AS ENUM ('phenotypic', 'inheritance', 'frequency', 'clinical');
CREATE TYPE phenotype_presence AS ENUM ('unknow', 'present', 'absent');


DROP TABLE IF EXISTS subject_phenotype CASCADE;
DROP TABLE IF EXISTS hpo_phenotype CASCADE;
DROP TABLE IF EXISTS hpo_disease CASCADE;

-- Create new hpo table
CREATE TABLE hpo_phenotype
(
    hpo_id character varying(10) COLLATE pg_catalog."C",
    parents character varying(10)[] COLLATE pg_catalog."C" DEFAULT NULL,
    childs character varying(10)[] COLLATE pg_catalog."C" DEFAULT NULL,
    label text COLLATE pg_catalog."C",
    definition text COLLATE pg_catalog."C",
    search text COLLATE pg_catalog."C",
    genes character varying(50)[] COLLATE pg_catalog."C" DEFAULT NULL,
    diseases character varying(30)[] COLLATE pg_catalog."C" DEFAULT NULL,
    allsubs_genes character varying(50)[] COLLATE pg_catalog."C" DEFAULT NULL,
    allsubs_diseases character varying(30)[] COLLATE pg_catalog."C" DEFAULT NULL,
    category phenotype_category DEFAULT 'phenotypic',
    meta JSON
);
CREATE TABLE hpo_disease
(
    hpo_id character varying(30) COLLATE pg_catalog."C",
    label text COLLATE pg_catalog."C",
    search text COLLATE pg_catalog."C",
    genes character varying(50)[] COLLATE pg_catalog."C" DEFAULT NULL,
    phenotypes character varying(10)[] COLLATE pg_catalog."C" DEFAULT NULL,
    phenotypes_neg character varying(10)[] COLLATE pg_catalog."C" DEFAULT NULL,
    meta JSON
); 

CREATE INDEX hpo_phenotype_idx 
    ON hpo_phenotype 
    USING btree (hpo_id);
CREATE INDEX hpo_disease_idx 
    ON hpo_disease 
    USING btree (hpo_id);
    

-- Create new phenotype table
CREATE TABLE subject_phenotype
(
    subject_id integer NOT NULL,
    hpo_id character varying(50) COLLATE pg_catalog."C" NOT NULL,
    presence phenotype_presence DEFAULT 'present',
    added_date timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT sp_pkey PRIMARY KEY (subject_id, hpo_id)
);


-- Update database version
UPDATE parameter SET value='9.0' WHERE key='database_version';
INSERT INTO "event" (message, type) VALUES ('Update database to version 9.0', 'technical');