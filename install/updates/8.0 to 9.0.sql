
-- Create new hpo table
CREATE TABLE hpo_term
(
    hpo_id character varying(10) COLLATE pg_catalog."C",
    parent character varying(10) COLLATE pg_catalog."C" DEFAULT NULL,
    childs character varying(10)[] COLLATE pg_catalog."C" DEFAULT NULL,
    label text COLLATE pg_catalog."C",
    definition text COLLATE pg_catalog."C",
    search text COLLATE pg_catalog."C"
);

CREATE INDEX hpo_term_idx 
    ON hpo_term 
    USING btree (hpo_id);



-- Update database version
UPDATE parameter SET value='9.0' WHERE key='database_version';
INSERT INTO "event" (message, type) VALUES ('Update database to version 9.0', 'technical');