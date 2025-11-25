# Supabase Setup Guide

This guide will help you set up Supabase for the EasyExcel backend.

## Step 1: Create a Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up for a free account (or log in if you already have one)
3. Create a new project

## Step 2: Get Your Supabase Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. You'll find:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **Service Role Key** (keep this secret! This is your `SUPABASE_KEY`)

## Step 3: Create Database Tables

1. In your Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy and paste the contents of `backend/supabase_schema.sql`
4. Click **Run** to execute the SQL

This will create:
- `users` table - stores user accounts and API keys
- `subscriptions` table - stores subscription information
- `token_usage` table - tracks token usage history
- Indexes for better performance
- Row Level Security policies

## Step 4: Configure Environment Variables

Add these to your `.env` file (both local and on your Droplet):

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

**Important Notes:**
- Use the **Service Role Key** (not the anon key) for backend access
- The Service Role Key bypasses Row Level Security, which is needed for your backend
- Keep this key secret and never commit it to git

## Step 5: Install Dependencies

On your local machine:
```bash
cd backend
pip install -r requirements.txt
```

On your DigitalOcean Droplet:
```bash
cd /opt/easyexcel-backend
source venv/bin/activate
pip install -r requirements.txt
```

## Step 6: Test the Connection

The backend will automatically connect to Supabase when it starts. Check the logs:

```bash
# On Droplet
journalctl -u easyexcel-backend -f
```

You should see: `"Supabase client initialized successfully."`

## Step 7: Migrate Existing Data (Optional)

If you have existing SQLite data, you can migrate it:

1. Export data from SQLite:
```python
# Run this script to export data
python backend/migrate_to_supabase.py
```

2. Or manually copy data using Supabase dashboard → Table Editor

## Troubleshooting

### Error: "Supabase credentials not found"
- Make sure `SUPABASE_URL` and `SUPABASE_KEY` are set in your `.env` file
- Check for extra spaces or quotes in the values

### Error: "Failed to initialize Supabase client"
- Verify your `SUPABASE_URL` is correct (should end with `.supabase.co`)
- Verify your `SUPABASE_KEY` is the Service Role Key (starts with `eyJ...`)

### Tables not found
- Make sure you ran the SQL schema in Step 3
- Check Supabase dashboard → Table Editor to verify tables exist

### Permission denied
- Make sure you're using the **Service Role Key**, not the anon key
- Check Row Level Security policies in Supabase dashboard

## Next Steps

After setting up Supabase:
1. ✅ Test user registration: `POST /api/users/register`
2. ✅ Test API key authentication
3. ✅ Test subscription creation
4. ✅ Monitor token usage in Supabase dashboard

## Supabase Dashboard Features

You can monitor your app in the Supabase dashboard:
- **Table Editor**: View and edit data
- **SQL Editor**: Run custom queries
- **Logs**: View API requests and errors
- **Database**: View table structure and relationships

## Free Tier Limits

Supabase free tier includes:
- 500 MB database storage
- 2 GB bandwidth
- 50,000 monthly active users
- Unlimited API requests

This should be sufficient for most use cases. Upgrade if you need more.



