-- Repid Database Cleanup Script - OLD SCHEMA ONLY
-- This drops only the previously created tables:
-- - app_users
-- - voice_instructions
-- - workout_packages
-- - workout_steps
-- 
-- WARNING: This will delete these tables, functions, triggers, policies, and data
-- Use with caution! This is a destructive operation.
-- Run this in your Supabase SQL Editor before running the new schema migration

-- ============================================================================
-- DROP TRIGGERS
-- ============================================================================

-- Drop triggers (must be dropped before tables/functions)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS update_app_users_updated_at ON app_users;
DROP TRIGGER IF EXISTS update_workout_packages_updated_at ON workout_packages;
DROP TRIGGER IF EXISTS update_workout_steps_updated_at ON workout_steps;
DROP TRIGGER IF EXISTS update_voice_instructions_updated_at ON voice_instructions;

-- ============================================================================
-- DROP POLICIES (RLS)
-- ============================================================================

-- Drop policies for app_users
DROP POLICY IF EXISTS "Users can view own profile" ON app_users;
DROP POLICY IF EXISTS "Users can insert own profile" ON app_users;
DROP POLICY IF EXISTS "Users can update own profile" ON app_users;
DROP POLICY IF EXISTS "Users can delete own profile" ON app_users;

-- Drop policies for workout_packages
DROP POLICY IF EXISTS "Allow public read access to workout_packages" ON workout_packages;
DROP POLICY IF EXISTS "Allow authenticated users to insert workout_packages" ON workout_packages;
DROP POLICY IF EXISTS "Allow authenticated users to update workout_packages" ON workout_packages;
DROP POLICY IF EXISTS "Allow authenticated users to delete workout_packages" ON workout_packages;

-- Drop policies for workout_steps
DROP POLICY IF EXISTS "Allow public read access to workout_steps" ON workout_steps;
DROP POLICY IF EXISTS "Allow authenticated users to insert workout_steps" ON workout_steps;
DROP POLICY IF EXISTS "Allow authenticated users to update workout_steps" ON workout_steps;
DROP POLICY IF EXISTS "Allow authenticated users to delete workout_steps" ON workout_steps;

-- Drop policies for voice_instructions
DROP POLICY IF EXISTS "Allow public read access to voice_instructions" ON voice_instructions;
DROP POLICY IF EXISTS "Allow authenticated users to insert voice_instructions" ON voice_instructions;
DROP POLICY IF EXISTS "Allow authenticated users to update voice_instructions" ON voice_instructions;
DROP POLICY IF EXISTS "Allow authenticated users to delete voice_instructions" ON voice_instructions;

-- ============================================================================
-- DROP INDEXES
-- ============================================================================

-- Drop indexes for app_users
DROP INDEX IF EXISTS idx_app_users_email;

-- Drop indexes for workout_steps
DROP INDEX IF EXISTS idx_workout_steps_package_id;
DROP INDEX IF EXISTS idx_workout_steps_step_order;

-- Drop indexes for voice_instructions
DROP INDEX IF EXISTS idx_voice_instructions_step_id;

-- ============================================================================
-- DROP FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Drop foreign key constraint on workout_steps
ALTER TABLE workout_steps DROP CONSTRAINT IF EXISTS fk_voice_instruction;

-- ============================================================================
-- DROP TABLES
-- ============================================================================
-- Drop tables in reverse dependency order (child tables first)

DROP TABLE IF EXISTS voice_instructions CASCADE;
DROP TABLE IF EXISTS workout_steps CASCADE;
DROP TABLE IF EXISTS workout_packages CASCADE;
DROP TABLE IF EXISTS app_users CASCADE;

-- ============================================================================
-- DROP FUNCTIONS
-- ============================================================================

DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- Uncomment the following to verify cleanup (should not show the old tables)

-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('app_users', 'voice_instructions', 'workout_packages', 'workout_steps');
