DROP TABLE IF EXISTS hpo_phenotype;
CREATE TABLE hpo_phenotype
(
    hpo_id character varying(30) COLLATE pg_catalog."C",
    hpo_label text COLLATE pg_catalog."C",
    gene_id integer,
    gene_name character varying(255) COLLATE pg_catalog."C"
);

DROP TABLE IF EXISTS hpo_disease;
CREATE TABLE hpo_disease
(
    disease_id character varying(30) COLLATE pg_catalog."C",
    gene_name character varying(255) COLLATE pg_catalog."C",
    gene_id integer,
    hpo_id character varying(30) COLLATE pg_catalog."C",
    hpo_label text COLLATE pg_catalog."C"
); 

\COPY hpo_phenotype FROM '/var/regovar/databases/hpo_phenotype.txt' HEADER DELIMITER E'\t' CSV ;
\COPY hpo_disease FROM '/var/regovar/databases/hpo_disease.txt' HEADER DELIMITER E'\t' CSV;
