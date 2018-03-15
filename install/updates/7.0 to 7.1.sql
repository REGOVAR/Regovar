
-- Alter column type of event
ALTER TABLE "event" DROP COLUMN meta;
ALTER TABLE "event" ADD COLUMN meta JSONB;
ALTER TABLE "event" ADD COLUMN details text COLLATE pg_catalog."C";
ALTER TABLE "event" ADD COLUMN author_id int;

-- Rename columns
ALTER TABLE "pipeline" RENAME COLUMN developers TO developpers;
ALTER TABLE "pipeline" RENAME COLUMN pirus_api TO version_api;

-- Alter type type
ALTER TYPE "event_type" ADD VALUE IF NOT EXISTS 'custom'
ALTER TYPE "event_type" ADD VALUE IF NOT EXISTS 'technical'

-- New type
CREATE TYPE file_usage AS ENUM ('none', 'pipeline', 'job', 'subject', 'sample', 'analysis', 'mix');

-- Create index
CREATE INDEX event_meta_idx 
    ON "event"
    USING GIN (meta jsonb_path_ops);
    
-- Alter file table
ALTER TABLE file ADD COLUMN usage file_usage DEFAULT 'none';
UPDATE file AS f SET usage='pipeline' FROM pipeline AS p WHERE f.id=p.image_file_id;
UPDATE file AS f SET usage='job' FROM job_file AS j WHERE f.id=j.file_id;
UPDATE file AS f SET usage='subject' FROM subject_file AS s WHERE f.id=s.file_id;
UPDATE file AS f SET usage='sample' FROM sample AS s WHERE f.id=s.file_id;
UPDATE file AS f SET usage='analysis' FROM analysis_file AS a WHERE f.id=a.file_id;




-- Update database version
UPDATE parameter SET value='7.1' WHERE key='database_version';
INSERT INTO "event" (message, type) VALUES ('Update database to version 7.1', 'technical')