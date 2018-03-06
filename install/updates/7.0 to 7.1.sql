
-- Alter column type of event
ALTER TABLE "event" DROP COLUMN meta;
ALTER TABLE "event" ADD COLUMN meta JSONB;

-- Alter type type
ALTER TYPE "event_type" ADD VALUE IF NOT EXISTS 'custom'

-- Create index
CREATE INDEX event_meta_idx 
    ON "event"
    USING GIN (meta jsonb_path_ops);
    

-- Update database version
UPDATE parameter SET value='7.1' WHERE key='database_version';