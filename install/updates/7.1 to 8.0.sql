
-- Alter column type of event
ALTER TABLE "user" DROP COLUMN settings;
ALTER TABLE "user" DROP COLUMN roles;
ALTER TABLE "user" ADD COLUMN is_admin boolean DEFAULT True;

   
-- Update user table
UPDATE "user" SET is_admin=True WHERE id=1;



-- Update database version
UPDATE parameter SET value='8.0' WHERE key='database_version';
INSERT INTO "event" (message, type) VALUES ('Update database to version 8.0', 'technical');