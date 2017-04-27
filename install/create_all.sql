-- 
-- CREATE ALL - V1.0.0
--
CREATE TYPE event_type AS ENUM ('info', 'warning', 'error');
CREATE TYPE project_status AS ENUM ('open', 'closed');


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
    CONSTRAINT user_pkey PRIMARY KEY (id),
    CONSTRAINT user_ukey1 UNIQUE (login),
    CONSTRAINT user_ukey2 UNIQUE (email)
);
ALTER TABLE public.user OWNER TO regovar;


CREATE TABLE public.event
(
    id bigserial NOT NULL,
    "date" timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id integer,
    message text COLLATE pg_catalog."C",
    type event_type,

    project_id integer,
    analysis_id integer,
    file_id integer,
    subject_id integer,
    job_id integer,
    pipeline_id integer,
    CONSTRAINT event_pkey PRIMARY KEY (id)
);
ALTER TABLE public.event OWNER TO regovar;


CREATE TABLE public.project
(
    id serial NOT NULL,
    name character varying(255) COLLATE pg_catalog."C" NOT NULL,
    comment text,
    parent_id integer,
    status project_status,
    is_folder boolean,
    last_activity timestamp without time zone,
    CONSTRAINT project_pkey PRIMARY KEY (id)
);
ALTER TABLE public.project OWNER TO regovar;


CREATE TABLE public.user_project_sharing
(
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    write_authorisation boolean,
    CONSTRAINT ups_pkey PRIMARY KEY (project_id, user_id)
);
ALTER TABLE public.user_project_sharing OWNER TO regovar;






INSERT INTO "user" (login, firstname, lastname, roles) VALUES
  ('admin', "Root", "Administrator", '{"Administration": "Write"}'),
  ('o.gueudelot', 'Olivier', 'Gueudelot', '{"Administration": "Write"}'),
  ('as.denomme', 'Anne-Sophie', 'Denommé', '{}'),
  ('s.schutz', 'Sacha', 'Schutz', '{}'),
  ('j.roquet', 'Jérémie', 'Roquet', '{}');

INSERT INTO "event" (message, type) VALUES
  ('Regovar database creation', 'info');
