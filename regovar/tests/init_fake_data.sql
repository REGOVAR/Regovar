--
-- TEST PROJECT, INDICATOR AND USER
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
    ('sandbox U4', 'comment', NULL, False, True),
    ('folder',     'comment', NULL, True,  False),
    ('P1',         'comment', 5,    False, False),
    ('P2',         'comment', NULL, False, False);

INSERT INTO user_project_sharing (project_id, user_id, write_authorisation) VALUES
    (5, 3, True),
    (6, 3, False),
    (7, 3, True),
    (7, 4, True);
    
INSERT INTO indicator (name, description, default_value_id) VALUES
    ('I1', 'description', 2);

INSERT INTO indicator_value (indicator_id, name, description, style) VALUES
    (1, 'I1.1', 'description', '{"icon":"circle", "color":"#FF0000"}'),
    (1, 'I1.2', 'description', '{"icon":"circle", "color":"#00FF00"}'),
    (1, 'I1.3', 'description', '{"icon":"circle", "color":"#0000FF"}');

INSERT INTO project_indicator (indicator_id, project_id, indicator_value_id) VALUES
    (1, 6, 3),
    (1, 7, 1);



--
-- TEST SAMPLE AND SUBJECT
--
INSERT INTO subject (identifiant, firstname, lastname, sex) VALUES
    ('S1', 'firstname1', 'lastname1', 'male'),
    ('S2', 'firstname2', 'lastname2', 'female'),
    ('S3', NULL, NULL, NULL);
    
INSERT INTO sample (subject_id, name, is_mosaic, file_id, loading_progress, reference_id, status) VALUES
    (1, 'sp_1', False, 4, 1, 2, 'ready'),
    (2, 'sp_2', True,  4, 1, 2, 'ready'),
    (3, 'sp_3', True,  4, 1, 2, 'ready');

INSERT INTO user_subject_sharing (subject_id, user_id, write_authorisation) VALUES
    (1, 3, True),
    (1, 4, False),
    (2, 3, True),
    (2, 4, True);
    
INSERT INTO subject_file (subject_id, file_id) VALUES
    (1, 1),
    (1, 3),
    (2, 1);
    
INSERT INTO subject_indicator (indicator_id, subject_id, indicator_value_id) VALUES
    (1, 1, 3),
    (1, 3, 1);

INSERT INTO project_subject (project_id, subject_id) VALUES
    (6, 1),
    (6, 2),
    (7, 2),
    (7, 3);
    
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
    
INSERT INTO project_file (project_id, file_id) VALUES
    (6, 1),
    (6, 2);



--
-- TEST ANALYSIS (SAMPLE, ATTRIBUTES, FILTER, ...)
--


  
  
        
--
-- TEST EVENTS (with PROJECT, USER, SUBJECT, JOB, ANALYSIS, FILE)
--


        
--
-- TEST PANEL
--

















