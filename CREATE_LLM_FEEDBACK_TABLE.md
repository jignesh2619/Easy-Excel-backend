# Creating the LLM Feedback Table in Supabase

This guide shows you how to create the `llm_feedback` table in Supabase for tracking LLM execution feedback.

## Option 1: Using Supabase SQL Editor (Recommended)

1. **Go to your Supabase Dashboard**
   - Navigate to: https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New query"

3. **Run the SQL Script**
   - Copy and paste the following SQL:

```sql
-- LLM Feedback table for fine-tuning and learning
CREATE TABLE IF NOT EXISTS llm_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_prompt TEXT NOT NULL,
    action_plan JSONB NOT NULL,
    execution_result JSONB,
    error TEXT,
    success BOOLEAN NOT NULL,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_llm_feedback_success ON llm_feedback(success, created_at);
CREATE INDEX IF NOT EXISTS idx_llm_feedback_user_id ON llm_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_feedback_created_at ON llm_feedback(created_at);

-- Full-text search index for prompt similarity matching
CREATE INDEX IF NOT EXISTS idx_llm_feedback_prompt ON llm_feedback USING gin(to_tsvector('english', user_prompt));

-- Enable Row Level Security
ALTER TABLE llm_feedback ENABLE ROW LEVEL SECURITY;

-- Create policy to allow service role to access all data
CREATE POLICY "Service role can access llm_feedback" ON llm_feedback
    FOR ALL USING (true);
```

4. **Click "Run"** to execute the SQL

5. **Verify the Table**
   - Go to "Table Editor" in the left sidebar
   - You should see `llm_feedback` table listed

## Option 2: Using the Updated Schema File

The `supabase_schema.sql` file has been updated to include the `llm_feedback` table.

1. **Open `backend/supabase_schema.sql`**
2. **Copy the `llm_feedback` table definition** (lines for CREATE TABLE and indexes)
3. **Run it in Supabase SQL Editor** as shown in Option 1

## Table Structure

The `llm_feedback` table stores:

- **id**: Unique identifier (UUID)
- **user_prompt**: The original user prompt
- **action_plan**: The JSON action plan returned by LLM (stored as JSONB)
- **execution_result**: Result of execution (stored as JSONB, nullable)
- **error**: Error message if execution failed (nullable)
- **success**: Boolean indicating success/failure
- **user_id**: Optional reference to users table
- **created_at**: Timestamp of when feedback was recorded

## Indexes

The table has indexes for:
- Fast queries by success status and date
- Fast queries by user_id
- Fast queries by created_at
- Full-text search on user_prompt for similarity matching

## Usage

Once the table is created, the `FeedbackLearner` service will automatically:
- Record successful executions
- Record failed executions
- Retrieve similar examples for few-shot learning
- Analyze failure patterns
- Export training datasets

## Verification

To verify the table was created correctly:

```sql
-- Check table exists
SELECT * FROM llm_feedback LIMIT 1;

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'llm_feedback';
```

## Next Steps

After creating the table:

1. **Update your backend code** to use `FeedbackLearner` (already implemented in `services/feedback_learner.py`)
2. **Integrate feedback recording** in `services/llm_agent.py`
3. **Start collecting feedback** from real user interactions
4. **Use feedback for improvement** - the system will automatically learn from successful examples

## Security Note

The current policy allows full access. For production, you may want to restrict access:

```sql
-- More restrictive policy (example)
CREATE POLICY "Users can only see their own feedback" ON llm_feedback
    FOR SELECT USING (auth.uid()::text = user_id);
```

However, for backend service role access, the current policy is fine.

