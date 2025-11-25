# Supabase Credentials Setup

## Your Project Details:
- **Project ID**: `pkkfenvnpddfccoiiqef`
- **Supabase URL**: `https://pkkfenvnpddfccoiiqef.supabase.co`

## Important: You Need the Service Role Key

The key you provided (`sb_publishable_wnKILC3aL-vAl9Z2BmCIaw_gHFzKaSv`) is a **publishable key** (for frontend use).

For the backend, you need the **Service Role Key** which:
- Starts with `eyJ...` (much longer)
- Is found in Supabase Dashboard → Settings → API → "service_role" key
- **Keep this secret!** Never expose it in frontend code.

## Steps to Get Service Role Key:

1. Go to your Supabase project: https://supabase.com/dashboard/project/pkkfenvnpddfccoiiqef
2. Click **Settings** (gear icon) in the left sidebar
3. Click **API** under Project Settings
4. Scroll to **Project API keys**
5. Find the **`service_role`** key (it's hidden by default, click "Reveal")
6. Copy the entire key (it's very long, starts with `eyJ...`)

## Update Your .env File:

Once you have the Service Role Key, add these to your `.env` file:

```env
SUPABASE_URL=https://pkkfenvnpddfccoiiqef.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

Replace `your_service_role_key_here` with the actual Service Role Key.

## Where to Update:

1. **Local machine**: `backend/.env`
2. **DigitalOcean Droplet**: `/opt/easyexcel-backend/.env`

After updating, restart the backend service:
```bash
sudo systemctl restart easyexcel-backend
```



