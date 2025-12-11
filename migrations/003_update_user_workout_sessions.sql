-- Update user_workout_sessions table
-- Dropping columns: duration_sec, calories_estimated as requested

ALTER TABLE user_workout_sessions 
DROP COLUMN IF EXISTS duration_sec,
DROP COLUMN IF EXISTS calories_estimated;
