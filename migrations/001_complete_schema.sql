-- Repid Complete Schema
-- Consolidated migration for clean database setup
-- Run this migration in your Supabase SQL Editor

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLES
-- ============================================================================

-- Table: app_users
CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    avatar_url TEXT,
    email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: user_profile
CREATE TABLE IF NOT EXISTS user_profile (
    user_id UUID PRIMARY KEY REFERENCES app_users(id) ON DELETE CASCADE,
    height_cm INTEGER,
    weight_kg INTEGER,
    birthday DATE,
    sex TEXT CHECK (sex IN ('male', 'female', 'other')),
    fitness_level TEXT CHECK (fitness_level IN ('beginner', 'intermediate', 'advanced')),
    goal TEXT CHECK (goal IN ('lose_fat', 'build_muscle', 'general_fitness')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: user_app_config
CREATE TABLE IF NOT EXISTS user_app_config (
    user_id UUID PRIMARY KEY REFERENCES app_users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: user_trainer_config
CREATE TABLE IF NOT EXISTS user_trainer_config (
    user_id UUID PRIMARY KEY REFERENCES app_users(id) ON DELETE CASCADE,
    trainer_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: workout_packages
CREATE TABLE IF NOT EXISTS workout_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    estimated_duration_sec INTEGER,
    cover_image_url TEXT,
    voice_id UUID,
    user_id UUID REFERENCES app_users(id) ON DELETE SET NULL,
    step_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: workout_steps
CREATE TABLE IF NOT EXISTS workout_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    duration_sec INTEGER,
    posture_image_url TEXT,
    instructions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: user_workout_sessions
CREATE TABLE IF NOT EXISTS user_workout_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES app_users(id) ON DELETE CASCADE,
    package_id UUID REFERENCES workout_packages(id) ON DELETE SET NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_sec INTEGER,
    calories_estimated INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Foreign keys are already defined in table definitions above
-- Additional constraints can be added here if needed

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Indexes for app_users
CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email);

-- Indexes for user_profile
CREATE INDEX IF NOT EXISTS idx_user_profile_user_id ON user_profile(user_id);

-- Indexes for user_app_config
CREATE INDEX IF NOT EXISTS idx_user_app_config_user_id ON user_app_config(user_id);

-- Indexes for user_trainer_config
CREATE INDEX IF NOT EXISTS idx_user_trainer_config_user_id ON user_trainer_config(user_id);

-- Indexes for workout_packages
CREATE INDEX IF NOT EXISTS idx_workout_packages_user_id ON workout_packages(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_packages_voice_id ON workout_packages(voice_id);
CREATE INDEX IF NOT EXISTS idx_workout_packages_category ON workout_packages(category);

-- Indexes for workout_steps
-- GIN index for array operations on step_ids in workout_packages
CREATE INDEX IF NOT EXISTS idx_workout_packages_step_ids ON workout_packages USING GIN(step_ids);

-- Indexes for user_workout_sessions
CREATE INDEX IF NOT EXISTS idx_user_workout_sessions_user_id ON user_workout_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_workout_sessions_package_id ON user_workout_sessions(package_id);
CREATE INDEX IF NOT EXISTS idx_user_workout_sessions_started_at ON user_workout_sessions(started_at);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to handle new user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.app_users (id, full_name, email)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
    NEW.email
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Triggers for updated_at on app_users
CREATE TRIGGER update_app_users_updated_at 
    BEFORE UPDATE ON app_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers for updated_at on user_profile
CREATE TRIGGER update_user_profile_updated_at 
    BEFORE UPDATE ON user_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers for updated_at on user_app_config
CREATE TRIGGER update_user_app_config_updated_at 
    BEFORE UPDATE ON user_app_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers for updated_at on user_trainer_config
CREATE TRIGGER update_user_trainer_config_updated_at 
    BEFORE UPDATE ON user_trainer_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers for updated_at on workout_packages
CREATE TRIGGER update_workout_packages_updated_at 
    BEFORE UPDATE ON workout_packages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers for updated_at on workout_steps
CREATE TRIGGER update_workout_steps_updated_at 
    BEFORE UPDATE ON workout_steps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers for updated_at on user_workout_sessions
CREATE TRIGGER update_user_workout_sessions_updated_at 
    BEFORE UPDATE ON user_workout_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for new user creation
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on app_users
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;

-- Policies for app_users
CREATE POLICY "Users can view own profile"
  ON app_users
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON app_users
  FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON app_users
  FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can delete own profile"
  ON app_users
  FOR DELETE
  USING (auth.uid() = id);

-- Enable RLS on user_profile
ALTER TABLE user_profile ENABLE ROW LEVEL SECURITY;

-- Policies for user_profile
CREATE POLICY "Users can view own profile"
  ON user_profile
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
  ON user_profile
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
  ON user_profile
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own profile"
  ON user_profile
  FOR DELETE
  USING (auth.uid() = user_id);

-- Enable RLS on user_app_config
ALTER TABLE user_app_config ENABLE ROW LEVEL SECURITY;

-- Policies for user_app_config
CREATE POLICY "Users can view own config"
  ON user_app_config
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own config"
  ON user_app_config
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own config"
  ON user_app_config
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own config"
  ON user_app_config
  FOR DELETE
  USING (auth.uid() = user_id);

-- Enable RLS on user_trainer_config
ALTER TABLE user_trainer_config ENABLE ROW LEVEL SECURITY;

-- Policies for user_trainer_config
CREATE POLICY "Users can view own trainer config"
  ON user_trainer_config
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own trainer config"
  ON user_trainer_config
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own trainer config"
  ON user_trainer_config
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own trainer config"
  ON user_trainer_config
  FOR DELETE
  USING (auth.uid() = user_id);

-- Enable RLS on workout_packages
ALTER TABLE workout_packages ENABLE ROW LEVEL SECURITY;

-- Policies for workout_packages
CREATE POLICY "Allow public read access to workout_packages"
  ON workout_packages
  FOR SELECT
  USING (true);

CREATE POLICY "Allow authenticated users to insert workout_packages"
  ON workout_packages
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update own workout_packages"
  ON workout_packages
  FOR UPDATE
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can delete own workout_packages"
  ON workout_packages
  FOR DELETE
  USING (auth.uid() = user_id OR user_id IS NULL);

-- Enable RLS on workout_steps
ALTER TABLE workout_steps ENABLE ROW LEVEL SECURITY;

-- Policies for workout_steps
CREATE POLICY "Allow public read access to workout_steps"
  ON workout_steps
  FOR SELECT
  USING (true);

CREATE POLICY "Allow authenticated users to insert workout_steps"
  ON workout_steps
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to update workout_steps"
  ON workout_steps
  FOR UPDATE
  USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to delete workout_steps"
  ON workout_steps
  FOR DELETE
  USING (auth.role() = 'authenticated');

-- Enable RLS on user_workout_sessions
ALTER TABLE user_workout_sessions ENABLE ROW LEVEL SECURITY;

-- Policies for user_workout_sessions
CREATE POLICY "Users can view own workout sessions"
  ON user_workout_sessions
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own workout sessions"
  ON user_workout_sessions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workout sessions"
  ON user_workout_sessions
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own workout sessions"
  ON user_workout_sessions
  FOR DELETE
  USING (auth.uid() = user_id);
