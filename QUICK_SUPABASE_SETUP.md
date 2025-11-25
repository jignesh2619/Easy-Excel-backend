# Quick Supabase Setup - Your Credentials

## ✅ Your Supabase Credentials:
- **URL**: `https://pkkfenvnpddfccoiiqef.supabase.co`
- **Secret Key**: `sb_secret_N7Nelp809WFt5xk-QPHTOA_vkTcryTA`

## Step 1: Create Database Tables

1. Go to your Supabase Dashboard: https://supabase.com/dashboard/project/pkkfenvnpddfccoiiqef
2. Click **SQL Editor** in the left sidebar
3. Click **New Query**
4. Open `backend/supabase_schema.sql` and copy ALL its contents
5. Paste into the SQL Editor
6. Click **Run** (or press Ctrl+Enter)

You should see: "Success. No rows returned"

## Step 2: Update Local .env File

Add these lines to `backend/.env`:

```env
SUPABASE_URL=https://pkkfenvnpddfccoiiqef.supabase.co
SUPABASE_KEY=sb_secret_N7Nelp809WFt5xk-QPHTOA_vkTcryTA
```

## Step 3: Update Droplet .env File

**Option A: Use the update script (recommended)**

1. Copy `backend/UPDATE_SUPABASE_ENV.sh` to your Droplet
2. SSH into your Droplet
3. Run:
```bash
chmod +x /opt/easyexcel-backend/UPDATE_SUPABASE_ENV.sh
/opt/easyexcel-backend/UPDATE_SUPABASE_ENV.sh
```

**Option B: Manual edit**

1. SSH into your Droplet
2. Edit the file:
```bash
nano /opt/easyexcel-backend/.env
```
3. Add these lines:
```env
SUPABASE_URL=https://pkkfenvnpddfccoiiqef.supabase.co
SUPABASE_KEY=sb_secret_N7Nelp809WFt5xk-QPHTOA_vkTcryTA
```
4. Save: `Ctrl+O`, `Enter`, `Ctrl+X`

## Step 4: Install Supabase Dependencies

On your Droplet:
```bash
cd /opt/easyexcel-backend
source venv/bin/activate
pip install supabase postgrest
```

## Step 5: Restart Backend Service

```bash
sudo systemctl restart easyexcel-backend
```

## Step 6: Verify It's Working

Check the logs:
```bash
journalctl -u easyexcel-backend -f
```

You should see: `"Supabase client initialized successfully."`

## Test the API

Try registering a user:
```bash
curl -X POST http://165.227.29.127:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "plan": "Free"}'
```

You should get back a user object with an API key!

## Troubleshooting

**Error: "Supabase credentials not found"**
- Make sure you added both `SUPABASE_URL` and `SUPABASE_KEY` to `.env`
- Check for typos or extra spaces

**Error: "Failed to initialize Supabase client"**
- Verify the URL is correct
- Make sure you're using the secret key (not publishable key)
- Check Supabase dashboard to ensure project is active

**Tables not found**
- Make sure you ran the SQL schema in Step 1
- Check Supabase dashboard → Table Editor to verify tables exist



