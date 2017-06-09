
-- 
-- CREATE ALL - V0.2.0
--


--
-- Assuming that Regovar is based on Pirus and Annso models
--
ALTER TABLE public.analysis ADD COLUMN owner_id integer;
ALTER TABLE public.analysis ADD COLUMN project_id integer;
ALTER TABLE public.pipeline ADD COLUMN starred boolean;
ALTER TABLE sample ADD COLUMN subject_id integer;








-- 
-- REGOVAR PART - v 0.1.0
--


CREATE TYPE event_type AS ENUM ('info', 'warning', 'error');



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
    comment text COLLATE pg_catalog."C",
    parent_id integer,
    is_folder boolean,
    last_activity timestamp without time zone,
    is_sandbox boolean DEFAULT False,
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
    style text COLLATE pg_catalog."C",
    CONSTRAINT iv_pkey PRIMARY KEY (id)
);
CREATE TABLE public.project_indicator
(
    indicator_id integer NOT NULL,
    project_id integer,
    subject_id integer,
    analysis_id integer,
    file_id integer,
    indicator_value_id integer NOT NULL,
    CONSTRAINT pi_pkey PRIMARY KEY (project_id, subject_id, analysis_id, file_id, indicator_id)
);




--
-- INIT DATA
--
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
