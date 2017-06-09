


INSERT INTO file (name, type, size, upload_offset, status, job_source_id) VALUES
    ('TestPipeImage1.tar.xz', 'tar.xz', 30000, 30000, 'uploaded', NULL),
    ('TestPipeImage2.tar.xz', 'tar.xz', 30000, 20000, 'uploading', NULL),
    ('TestFile 1.bin', 'bin', 100000, 100000, 'checked', NULL),
    ('TestFile 2.vcf', 'vcf', 100000, 100000, 'checked', 1);


INSERT INTO pipeline (name, type, status, description, developers, image_file_id, manifest, documents) VALUES
    ('TestPipeline 1', 'github', 'ready', 'Pipe description', '["ikit", "dridk"]', 1, '{}', '[]'),
    ('TestPipeline 2', 'lxd', 'installing', 'Pipe description', '["oodnadata"]', 2, NULL, NULL);

INSERT INTO job (pipeline_id, name, config, status, progress_value, progress_label) VALUES
    (1, 'TestJob 1', '{}', 'done', 1, '100%'),
    (1, 'TestJob 2', '{}', 'pause', 0.5, 'Step : 4/8');


INSERT INTO job_file (job_id, file_id, as_input) VALUES
    (1, 3, TRUE),
    (1, 4, FALSE);