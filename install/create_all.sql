-- 
-- CREATE ALL - V1.0.0
--



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
    CONSTRAINT user_pkey PRIMARY KEY (id),
    CONSTRAINT user_ukey1 UNIQUE (login),
    CONSTRAINT user_ukey2 UNIQUE (email)
);
ALTER TABLE public.user OWNER TO regovar;



INSERT INTO "user" (login, role) VALUES
  ('admin', '{"Administration": "Write"}');
