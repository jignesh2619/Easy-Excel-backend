-- Migration Script for Supabase Auth Integration
-- Run this in your Supabase SQL Editor to add the new column

-- Step 1: Add supabase_auth_id column (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'supabase_auth_id'
    ) THEN
        ALTER TABLE users ADD COLUMN supabase_auth_id TEXT UNIQUE;
    END IF;
END $$;

-- Step 2: Make api_key nullable (if it's currently NOT NULL)
DO $$ 
BEGIN
    -- Check if api_key has NOT NULL constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu 
        ON tc.constraint_name = ccu.constraint_name
        WHERE tc.table_name = 'users' 
        AND tc.constraint_type = 'NOT NULL'
        AND ccu.column_name = 'api_key'
    ) THEN
        ALTER TABLE users ALTER COLUMN api_key DROP NOT NULL;
    END IF;
END $$;

-- Step 3: Create index for supabase_auth_id (if it doesn't exist)
CREATE INDEX IF NOT EXISTS idx_users_supabase_auth_id ON users(supabase_auth_id);

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('supabase_auth_id', 'api_key')
ORDER BY column_name;

