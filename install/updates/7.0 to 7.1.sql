
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

-- Create index
CREATE INDEX event_meta_idx 
    ON "event"
    USING GIN (meta jsonb_path_ops);
    

-- Update database version
UPDATE parameter SET value='7.1' WHERE key='database_version';
INSERT INTO "event" (message, type) VALUES ('Update database to version 7.1', 'technical')