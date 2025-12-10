-- Insert initial workout steps (must be inserted first since packages reference them)
INSERT INTO workout_steps (id, title, description, duration_sec, posture_image_url, instructions)
VALUES
('829ddd38-d44d-4458-b5fc-3fe666a2c950', 'Jumping Jacks', 'Warm up with jumping jacks', 60, 'https://dummyimage.com/600x400/000/fff&text=test1', NULL),
('0cfa6d1b-3bd6-4a81-9326-594a4d683530', 'Push Ups', 'Standard push ups', 90, 'https://dummyimage.com/600x400/000/fff&text=test2', NULL),
('805d2436-5644-42db-b225-f4888f0b5020', 'Plank', 'Hold plank position', 60, 'https://dummyimage.com/600x400/000/fff&text=test3', NULL),
('62dfe486-ebdb-443e-9092-58d82568aee3', 'Bicep Curls', 'Dumbbell bicep curls', 120, 'https://dummyimage.com/600x400/000/fff&text=test4', NULL);

-- Insert initial workout packages
INSERT INTO workout_packages (id, title, description, category, estimated_duration_sec, cover_image_url, voice_id, step_ids)
VALUES
('3acf81ed-7233-4491-bfe1-56711b74d314', 'Full Body Beginner', 'A 20-minute beginner full body workout', 'Full Body', 1200, 'https://dummyimage.com/600x400/000/fff&text=test5', NULL, ARRAY['829ddd38-d44d-4458-b5fc-3fe666a2c950', '0cfa6d1b-3bd6-4a81-9326-594a4d683530']::UUID[]),
('374b266b-47dc-4113-abb5-845677494dc3', 'Core Strength', 'Focus on core muscles', 'Core', 900, 'https://dummyimage.com/600x400/000/fff&text=test6', NULL, ARRAY['805d2436-5644-42db-b225-f4888f0b5020']::UUID[]),
('28086594-cdc7-4caf-b617-a5fcaeb2d987', 'Upper Body Blast', 'Intense upper body session', 'Upper Body', 1500, 'https://dummyimage.com/600x400/000/fff&text=test7', NULL, ARRAY['62dfe486-ebdb-443e-9092-58d82568aee3']::UUID[]);
