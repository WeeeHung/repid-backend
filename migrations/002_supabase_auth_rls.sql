-- Supabase Auth RLS Policies
-- This migration enables Row Level Security (RLS) on existing tables
-- to work with Supabase authentication

-- Enable RLS on workout_packages
ALTER TABLE workout_packages ENABLE ROW LEVEL SECURITY;

-- Create policy for selecting workout packages (public read for now, can be restricted later)
CREATE POLICY "Allow public read access to workout_packages"
  ON workout_packages
  FOR SELECT
  USING (true);

-- Create policy for inserting workout packages (authenticated users only)
CREATE POLICY "Allow authenticated users to insert workout_packages"
  ON workout_packages
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- Create policy for updating workout packages (authenticated users only)
CREATE POLICY "Allow authenticated users to update workout_packages"
  ON workout_packages
  FOR UPDATE
  USING (auth.role() = 'authenticated');

-- Create policy for deleting workout packages (authenticated users only)
CREATE POLICY "Allow authenticated users to delete workout_packages"
  ON workout_packages
  FOR DELETE
  USING (auth.role() = 'authenticated');

-- Enable RLS on workout_steps
ALTER TABLE workout_steps ENABLE ROW LEVEL SECURITY;

-- Create policy for selecting workout steps (public read for now)
CREATE POLICY "Allow public read access to workout_steps"
  ON workout_steps
  FOR SELECT
  USING (true);

-- Create policy for inserting workout steps (authenticated users only)
CREATE POLICY "Allow authenticated users to insert workout_steps"
  ON workout_steps
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- Create policy for updating workout steps (authenticated users only)
CREATE POLICY "Allow authenticated users to update workout_steps"
  ON workout_steps
  FOR UPDATE
  USING (auth.role() = 'authenticated');

-- Create policy for deleting workout steps (authenticated users only)
CREATE POLICY "Allow authenticated users to delete workout_steps"
  ON workout_steps
  FOR DELETE
  USING (auth.role() = 'authenticated');

-- Enable RLS on voice_instructions
ALTER TABLE voice_instructions ENABLE ROW LEVEL SECURITY;

-- Create policy for selecting voice instructions (public read for now)
CREATE POLICY "Allow public read access to voice_instructions"
  ON voice_instructions
  FOR SELECT
  USING (true);

-- Create policy for inserting voice instructions (authenticated users only)
CREATE POLICY "Allow authenticated users to insert voice_instructions"
  ON voice_instructions
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- Create policy for updating voice instructions (authenticated users only)
CREATE POLICY "Allow authenticated users to update voice_instructions"
  ON voice_instructions
  FOR UPDATE
  USING (auth.role() = 'authenticated');

-- Create policy for deleting voice instructions (authenticated users only)
CREATE POLICY "Allow authenticated users to delete voice_instructions"
  ON voice_instructions
  FOR DELETE
  USING (auth.role() = 'authenticated');

