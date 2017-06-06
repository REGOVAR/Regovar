
-- 
-- CREATE ALL - V0.2.0
--


--
-- Assuming that Regovar is based on Pirus and Annso models
--
ALTER TABLE public.analysis ADD COLUMN owner_id integer;
ALTER TABLE public.analysis ADD COLUMN project_id integer;










-- 
-- REGOVAR PART - v 0.1.0
--


CREATE TYPE event_type AS ENUM ('info', 'warning', 'error');



CREATE TABLE public.user
(
    id serial NOT NULL,
    login character varying(255) COLLATE pg_catalog."C" NOT NULL,
    password character varying(255) COLLATE pg_catalog."C",
    email character varying(255) COLLATE pg_catalog."C",
    firstname character varying(255) COLLATE pg_catalog."C",
    lastname character varying(255) COLLATE pg_catalog."C",
    function text COLLATE pg_catalog."C",
    location text COLLATE pg_catalog."C",
    last_activity timestamp without time zone,
    settings text COLLATE pg_catalog."C",
    roles text COLLATE pg_catalog."C",
    is_activated boolean DEFAULT True,
    sandbox_id integer,
    CONSTRAINT user_pkey PRIMARY KEY (id),
    CONSTRAINT user_ukey1 UNIQUE (login),
    CONSTRAINT user_ukey2 UNIQUE (email)
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


CREATE TABLE public.project
(
    id serial NOT NULL,
    name character varying(255) COLLATE pg_catalog."C",
    comment text,
    parent_id integer,
    is_folder boolean,
    last_activity timestamp without time zone,
    CONSTRAINT project_pkey PRIMARY KEY (id)
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









--
-- INIT DATA
--


INSERT INTO "project" (comment) VALUES
  ('My sandbox');
INSERT INTO "user" (login, firstname, lastname, roles, sandbox_id) VALUES
  ('admin', 'Root', 'Administrator', '{"Administration": "Write"}', 1);






INSERT INTO "event" (message, type) VALUES
  ('Regovar database creation', 'info'),
  ('Default root admin user created', 'info');
