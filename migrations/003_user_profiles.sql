-- User Profiles RLS Policies and Trigger Fix
-- This migration adds RLS policies to app_users and fixes the trigger function
-- to work properly with Row Level Security enabled

-- Enable RLS on app_users (if not already enabled)
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;

-- Drop existing trigger and function if they exist (to recreate with proper security)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- Recreate the function with SECURITY DEFINER so it can insert even with RLS enabled
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.app_users (id, full_name)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Recreate the trigger
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Add RLS policies for app_users
-- Users can view their own profile
CREATE POLICY "Users can view own profile"
  ON app_users
  FOR SELECT
  USING (auth.uid() = id);

-- Users can insert their own profile (for the trigger, but also allows manual inserts)
CREATE POLICY "Users can insert own profile"
  ON app_users
  FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON app_users
  FOR UPDATE
  USING (auth.uid() = id);

-- Users can delete their own profile
CREATE POLICY "Users can delete own profile"
  ON app_users
  FOR DELETE
  USING (auth.uid() = id);

-- Add updated_at column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'app_users' AND column_name = 'updated_at'
  ) THEN
    ALTER TABLE app_users ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
  END IF;
END $$;

-- Add email column if it doesn't exist (useful to have)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'app_users' AND column_name = 'email'
  ) THEN
    ALTER TABLE app_users ADD COLUMN email TEXT;
    -- Backfill email from auth.users if possible
    UPDATE app_users 
    SET email = (SELECT email FROM auth.users WHERE auth.users.id = app_users.id)
    WHERE email IS NULL;
  END IF;
END $$;

-- Create trigger for updated_at if the function exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column'
  ) THEN
    DROP TRIGGER IF EXISTS update_app_users_updated_at ON app_users;
    CREATE TRIGGER update_app_users_updated_at 
      BEFORE UPDATE ON app_users
      FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
  END IF;
END $$;

-- Update the trigger function to also set email
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

-- Create index on email for faster lookups (if it doesn't exist)
CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email);

