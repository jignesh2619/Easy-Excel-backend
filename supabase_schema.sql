-- Supabase Database Schema for EasyExcel
-- Run this SQL in your Supabase SQL Editor

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    supabase_auth_id TEXT UNIQUE,  -- Supabase Auth user ID
    email TEXT UNIQUE NOT NULL,
    api_key TEXT UNIQUE,  -- Legacy API key support (nullable for Supabase Auth users)
    plan TEXT NOT NULL DEFAULT 'Free',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paypal_subscription_id TEXT UNIQUE,
    plan_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    tokens_used INTEGER DEFAULT 0,
    tokens_limit INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Token usage tracking table
CREATE TABLE IF NOT EXISTS token_usage (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tokens_used INTEGER NOT NULL,
    operation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
CREATE INDEX IF NOT EXISTS idx_users_supabase_auth_id ON users(supabase_auth_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_token_usage_user_id ON token_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_created_at ON token_usage(created_at);

-- Enable Row Level Security (RLS) - Optional but recommended
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE token_usage ENABLE ROW LEVEL SECURITY;

-- Create policies to allow service role to access all data
-- Note: These policies allow full access. Adjust based on your security needs.
CREATE POLICY "Service role can access users" ON users
    FOR ALL USING (true);

CREATE POLICY "Service role can access subscriptions" ON subscriptions
    FOR ALL USING (true);

CREATE POLICY "Service role can access token_usage" ON token_usage
    FOR ALL USING (true);



