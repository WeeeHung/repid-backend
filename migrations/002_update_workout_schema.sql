-- Migration: Update workout_packages and workout_steps tables
-- Based on schema_plan.txt

-- ============================================================================
-- Update workout_packages
-- ============================================================================

-- Remove obsolete columns
ALTER TABLE workout_packages 
DROP COLUMN IF EXISTS voice_id;

-- We are replacing step_ids (UUID[]) with steps (JSONB)
-- If you want to preserve data, you might want to migrate it first. 
-- For now, we drop the old column and add the new one.
ALTER TABLE workout_packages 
DROP COLUMN IF EXISTS step_ids;

-- Add new steps column
ALTER TABLE workout_packages 
ADD COLUMN IF NOT EXISTS steps JSONB DEFAULT '[]';


-- ============================================================================
-- Update workout_steps
-- ============================================================================

-- Rename columns to match new schema
-- Using DO block to handle renames safely if columns already renamed
DO $$
BEGIN
    IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name = 'workout_steps' AND column_name = 'duration_sec') THEN
        ALTER TABLE workout_steps RENAME COLUMN duration_sec TO estimated_duration_sec;
    END IF;

    IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name = 'workout_steps' AND column_name = 'posture_image_url') THEN
        ALTER TABLE workout_steps RENAME COLUMN posture_image_url TO media_url;
    END IF;
END $$;

-- Add new columns
ALTER TABLE workout_steps 
ADD COLUMN IF NOT EXISTS category TEXT;

-- Add exercise_type with check constraint
-- We add the column first, then the constraint to ensure idempotency if possible, 
-- though adding constraint directly in ADD COLUMN is fine if column doesn't exist.
ALTER TABLE workout_steps 
ADD COLUMN IF NOT EXISTS exercise_type TEXT;

-- Add check constraint if it doesn't exist (namespaced constraint names are good practice)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'workout_steps_exercise_type_check') THEN
        ALTER TABLE workout_steps 
        ADD CONSTRAINT workout_steps_exercise_type_check 
        CHECK (exercise_type IN ('reps', 'duration', 'weight', 'distance', 'custom'));
    END IF;
END $$;

-- Add default value configuration columns
ALTER TABLE workout_steps 
ADD COLUMN IF NOT EXISTS default_reps INTEGER,
ADD COLUMN IF NOT EXISTS default_duration_sec INTEGER,
ADD COLUMN IF NOT EXISTS default_weight_kg DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS default_distance_m DOUBLE PRECISION;
