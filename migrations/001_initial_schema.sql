-- Repid MVP Initial Schema
-- Run this migration in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: workout_packages
CREATE TABLE IF NOT EXISTS workout_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    estimated_duration_sec INTEGER,
    cover_image_url TEXT,
    voice_pack_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: workout_steps
CREATE TABLE IF NOT EXISTS workout_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    package_id UUID NOT NULL REFERENCES workout_packages(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    duration_sec INTEGER NOT NULL,
    posture_image_url TEXT,
    voice_instruction_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(package_id, step_order)
);

-- Table: voice_instructions
CREATE TABLE IF NOT EXISTS voice_instructions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    step_id UUID NOT NULL REFERENCES workout_steps(id) ON DELETE CASCADE,
    tts_provider TEXT NOT NULL,
    audio_url TEXT NOT NULL,
    transcript TEXT NOT NULL,
    duration_sec INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key constraint for voice_instruction_id in workout_steps
ALTER TABLE workout_steps 
ADD CONSTRAINT fk_voice_instruction 
FOREIGN KEY (voice_instruction_id) 
REFERENCES voice_instructions(id) 
ON DELETE SET NULL;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_workout_steps_package_id ON workout_steps(package_id);
CREATE INDEX IF NOT EXISTS idx_workout_steps_step_order ON workout_steps(package_id, step_order);
CREATE INDEX IF NOT EXISTS idx_voice_instructions_step_id ON voice_instructions(step_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_workout_packages_updated_at BEFORE UPDATE ON workout_packages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workout_steps_updated_at BEFORE UPDATE ON workout_steps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_voice_instructions_updated_at BEFORE UPDATE ON voice_instructions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

