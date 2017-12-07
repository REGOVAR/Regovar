--
-- Fake users
--
INSERT INTO "user" (login, email, firstname, lastname, function, location, settings, roles, is_activated, sandbox_id) VALUES
    -- WARNING, Admin user added by default, so, id=1 is already created
    ('U2', 'user2@email.com', 'firstname2', 'lastname2', 'f2', 'l2', '{"fullscreen": true}', '{"Administration": "Read"}', True, 2),
    ('U3', 'user3@email.com', 'firstname3', 'lastname3', 'f3', 'l3', '{"fullscreen": true}', '{}',                         True, 3),
    ('U4', 'user4@email.com', 'firstname4', 'lastname4', 'f4', 'l4', NULL,                   '{}',                         False,4);

INSERT INTO project (name, comment, parent_id, is_folder, is_sandbox) VALUES
     -- WARNING, Admin user added by default, so, id=1 is already created for the sandbox project of the admin
    ('sandbox U2', 'comment', NULL, False, True),
    ('sandbox U3', 'comment', NULL, False, True),
    ('sandbox U4', 'comment', NULL, False, True);

    


--
-- Fake projects
--
INSERT INTO project (name, comment, parent_id, is_folder, is_sandbox) VALUES
    ('folder',     'comment', NULL, True,  False),
    ('P1',         'comment', 5,    False, False),
    ('P2',         'comment', NULL, False, False);










--
-- Fake subjects and samples
--
INSERT INTO subject (identifier, firstname, lastname, sex) VALUES
    ('S1', 'firstname1', 'lastname1', 'male'),
    ('S2', 'firstname2', 'lastname2', 'female');
    
INSERT INTO sample (subject_id, name, is_mosaic, file_id, loading_progress, reference_id, status) VALUES
    (1,    'sp_1', False, 3, 1, 2, 'ready'),
    (1,    'sp_2', False, 4, 1, 2, 'ready'),
    (NULL, 'sp_3', True,  1, 1, 2, 'ready');

    
    
INSERT INTO subject_indicator_value (subject_id, indicator_id, value) VALUES
    (1, 1, 'Urgent'),
    (2, 1, 'Low');






--
-- TEST FILE PIPELINE AND JOB
--
INSERT INTO file (name, type, size, upload_offset, status, job_source_id) VALUES
    ('F1.tar.xz', 'tar.xz', 30000,  30000,  'uploaded',  NULL),
    ('F2.tar.xz', 'tar.xz', 30000,  20000,  'uploading', NULL),
    ('F3.bin',    'bin',    100000, 100000, 'checked',   NULL),
    ('F4.vcf',    'vcf',    100000, 100000, 'checked',   1);

INSERT INTO pipeline (name, type, status, description, developers, image_file_id, manifest, documents) VALUES
    ('P1', 'github', 'ready',      'description', '["ikit", "dridk"]', 1, '{}', '[]'),
    ('P2', 'lxd',    'installing', 'description', '["oodnadata"]',     2, NULL, NULL);

INSERT INTO job (pipeline_id, project_id, name, config, status, progress_value, progress_label) VALUES
    (1, 6, 'J1', '{}', 'done',  1,   '100%'),
    (1, 6, 'J2', '{}', 'pause', 0.5, 'Step : 4/8');

INSERT INTO job_file (job_id, file_id, as_input) VALUES
    (1, 3, True),
    (1, 4, False);
    



--
-- TEST ANALYSIS (SAMPLE, ATTRIBUTES, FILTER, ...)
--


  
  
        
--
-- TEST EVENTS (with PROJECT, USER, SUBJECT, JOB, ANALYSIS, FILE)
--


        
--
-- TEST PANEL
--

















