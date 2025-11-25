# Deploy Backend to DigitalOcean App Platform

This guide will help you deploy your FastAPI backend to DigitalOcean App Platform.

## Prerequisites

1. A DigitalOcean account (sign up at https://www.digitalocean.com)
2. Your backend code ready to deploy
3. Environment variables configured

## Step 1: Create DigitalOcean App

### Option A: Using DigitalOcean Dashboard (Recommended)

1. **Log in to DigitalOcean**
   - Go to https://cloud.digitalocean.com
   - Sign in or create an account

2. **Create a New App**
   - Click "Create" → "Apps"
   - Choose "GitHub" or "GitLab" if you have your code in a repository
   - OR choose "Source Code" to upload directly

3. **Configure Your App**
   - **Name**: `easyexcel-backend` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Source**: 
     - If using GitHub/GitLab: Select your repository and branch
     - If uploading: Upload your `backend` folder as a zip file

4. **Configure Build Settings**
   - **Build Command**: Leave empty (DigitalOcean auto-detects Python)
   - **Run Command**: `python start_server.py`
   - **Environment**: Python 3.11 or 3.12

5. **Set Environment Variables**
   Click "Edit" next to Environment Variables and add:
   ```
   GEMINI_API_KEY=your_actual_gemini_key
   PORT=8080
   PAYPAL_CLIENT_ID=ATEF1de5CXpZ5E7PXmkXqqmFXor69bPrpJOrr9ZpHXH55ZlPWNmiYfJGDUOOaXTgIGSBN70P5EP4hfDL
   PAYPAL_CLIENT_SECRET=EIsw28kLVXE9u08OPsv8ZLQzzjVR9YgU_QBbvKmFNMA24xadoLrNNz3H0x47smXPJZ0AWRaHaIRjfKAr
   PAYPAL_MODE=sandbox
   PAYPAL_PLAN_ID_STARTER=your_starter_plan_id
   PAYPAL_PLAN_ID_PRO=your_pro_plan_id
   PAYPAL_RETURN_URL=https://your-frontend-domain.com/payment/success
   PAYPAL_CANCEL_URL=https://your-frontend-domain.com/payment/cancel
   ```

6. **Deploy**
   - Click "Create Resources"
   - Wait for deployment (5-10 minutes)
   - Your app will be available at: `https://your-app-name.ondigitalocean.app`

### Option B: Using DigitalOcean CLI (doctl)

1. **Install doctl**
   ```powershell
   # Using Chocolatey (if installed)
   choco install doctl
   
   # Or download from: https://github.com/digitalocean/doctl/releases
   ```

2. **Authenticate**
   ```powershell
   doctl auth init
   # Follow prompts to get your API token from: https://cloud.digitalocean.com/account/api/tokens
   ```

3. **Create App Spec File**
   Create `app.yaml` in your backend folder:
   ```yaml
   name: easyexcel-backend
   services:
   - name: api
     github:
       repo: your-username/your-repo
       branch: main
     run_command: python start_server.py
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     envs:
     - key: GEMINI_API_KEY
       value: your_actual_gemini_key
       scope: RUN_TIME
     - key: PORT
       value: "8080"
       scope: RUN_TIME
     - key: PAYPAL_CLIENT_ID
       value: ATEF1de5CXpZ5E7PXmkXqqmFXor69bPrpJOrr9ZpHXH55ZlPWNmiYfJGDUOOaXTgIGSBN70P5EP4hfDL
       scope: RUN_TIME
     - key: PAYPAL_CLIENT_SECRET
       value: EIsw28kLVXE9u08OPsv8ZLQzzjVR9YgU_QBbvKmFNMA24xadoLrNNz3H0x47smXPJZ0AWRaHaIRjfKAr
       scope: RUN_TIME
     - key: PAYPAL_MODE
       value: sandbox
       scope: RUN_TIME
   ```

4. **Deploy**
   ```powershell
   doctl apps create --spec app.yaml
   ```

## Step 2: Update start_server.py for DigitalOcean

DigitalOcean App Platform uses port 8080 by default. Update your `start_server.py`:

```python
port = int(os.getenv("PORT", "8080"))  # DigitalOcean uses 8080
```

## Step 3: Get Your Backend URL

After deployment, your backend will be available at:
- `https://your-app-name.ondigitalocean.app`

## Step 4: Update Frontend API URL

Update your frontend to point to the DigitalOcean backend:

1. **Find your frontend `.env` file** (or create one)
   - Location: `Onepagelandingpagedesign-main/Onepagelandingpagedesign-main/.env`

2. **Add/Update**:
   ```
   VITE_API_URL=https://your-app-name.ondigitalocean.app
   ```

3. **Redeploy your frontend** to Vercel

## Step 5: Configure PayPal Webhooks

1. **Get your webhook URL**:
   ```
   https://your-app-name.ondigitalocean.app/api/payments/webhook
   ```

2. **Add webhook in PayPal Dashboard**:
   - Go to https://developer.paypal.com/dashboard
   - Select your app
   - Go to "Webhooks"
   - Add webhook URL
   - Subscribe to events:
     - `BILLING.SUBSCRIPTION.CREATED`
     - `BILLING.SUBSCRIPTION.ACTIVATED`
     - `BILLING.SUBSCRIPTION.CANCELLED`
     - `PAYMENT.SALE.COMPLETED`

## Step 6: Test Your Deployment

1. **Health Check**:
   ```powershell
   curl https://your-app-name.ondigitalocean.app/health
   ```

2. **API Docs**:
   Visit: `https://your-app-name.ondigitalocean.app/docs`

## Troubleshooting

### App Won't Start
- Check logs in DigitalOcean dashboard
- Verify all environment variables are set
- Ensure `PORT` is set to `8080` (DigitalOcean default)

### 502 Bad Gateway
- Check if app is running (view logs)
- Verify `start_server.py` is using `PORT` environment variable
- Check if dependencies are installed correctly

### CORS Errors
- Update `app.py` CORS settings:
  ```python
  allow_origins=["https://your-frontend-domain.vercel.app"]
  ```

### Database Issues
- SQLite files are ephemeral on App Platform
- Consider using DigitalOcean Managed Database for production

## Pricing

DigitalOcean App Platform pricing:
- **Basic Plan**: $5/month (512MB RAM, 1GB storage)
- **Professional Plan**: $12/month (1GB RAM, 1GB storage)
- **Free tier**: Not available (unlike Railway/Render)

## Next Steps

1. ✅ Backend deployed to DigitalOcean
2. ✅ Frontend updated with backend URL
3. ✅ PayPal webhooks configured
4. ✅ Test end-to-end flow

## Support

- DigitalOcean Docs: https://docs.digitalocean.com/products/app-platform/
- DigitalOcean Community: https://www.digitalocean.com/community





