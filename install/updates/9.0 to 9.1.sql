


INSERT INTO parameter (key, value, description) VALUES 
('message', '{"type":"info", "message": ""}', 'Custom message to display on welcom screen on each client');

-- Update database version
UPDATE parameter SET value='9.1' WHERE key='database_version';
INSERT INTO "event" (message, type) VALUES ('Update database to version 9.1', 'technical');