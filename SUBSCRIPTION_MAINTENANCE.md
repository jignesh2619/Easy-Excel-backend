# Subscription Maintenance Setup

This document explains how to set up automatic subscription management for EasyExcel.

## Features Implemented

### 1. **Monthly Token Refresh for Free Users**
- Free users' tokens are automatically reset to 0 after 30 days
- The 30-day cycle resets each time tokens are refreshed
- Users get their full 200,000 tokens back every month

### 2. **Automatic Downgrade for Failed Payments**
- Pro/Starter users are automatically downgraded to Free if:
  - Their subscription expires (30+ days without renewal)
  - Payment fails (handled via PayPal webhooks)
  - Subscription is cancelled or suspended

### 3. **Payment Failure Handling**
- PayPal webhooks automatically trigger downgrades when:
  - `BILLING.SUBSCRIPTION.SUSPENDED` - Payment failed
  - `PAYMENT.SALE.DENIED` - Payment denied
  - `PAYMENT.CAPTURE.DENIED` - Payment capture failed
  - `BILLING.SUBSCRIPTION.CANCELLED` - User cancelled

## Setup Instructions

### Option 1: Cron Job (Recommended for VPS/Droplet)

Set up a daily cron job to call the maintenance endpoint:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 2 AM
0 2 * * * curl -X POST https://api.easyexcel.in/api/subscriptions/maintenance
```

Or use a more robust approach with error handling:

```bash
# Create a maintenance script
cat > /path/to/maintenance.sh << 'EOF'
#!/bin/bash
curl -X POST https://api.easyexcel.in/api/subscriptions/maintenance \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s -o /tmp/maintenance.log
EOF

chmod +x /path/to/maintenance.sh

# Add to crontab
0 2 * * * /path/to/maintenance.sh >> /var/log/easyexcel-maintenance.log 2>&1
```

### Option 2: GitHub Actions (Recommended for Cloud Deployments)

Create `.github/workflows/subscription-maintenance.yml`:

```yaml
name: Subscription Maintenance

on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch: # Allow manual trigger

jobs:
  maintenance:
    runs-on: ubuntu-latest
    steps:
      - name: Run Subscription Maintenance
        run: |
          curl -X POST ${{ secrets.API_URL }}/api/subscriptions/maintenance \
            -H "Content-Type: application/json"
```

Set `API_URL` secret in GitHub repository settings.

### Option 3: External Cron Service

Use services like:
- **cron-job.org** (free)
- **EasyCron** (free tier available)
- **UptimeRobot** (free monitoring + cron)

Configure them to POST to:
```
POST https://api.easyexcel.in/api/subscriptions/maintenance
```

### Option 4: DigitalOcean App Platform / Railway / Render

These platforms support scheduled tasks:

**DigitalOcean App Platform:**
Add to `app.yaml`:
```yaml
jobs:
  - name: subscription-maintenance
    source_dir: /
    github:
      repo: jignesh2619/Easy-Excel-backend
      branch: main
    run_command: python -c "import requests; requests.post('https://api.easyexcel.in/api/subscriptions/maintenance')"
    instance_count: 1
    instance_size_slug: basic-xxs
    schedule: "0 2 * * *"  # Daily at 2 AM
```

**Railway:**
Use Railway's Cron Jobs feature in the dashboard.

**Render:**
Use Render's Cron Jobs feature in the dashboard.

## Manual Testing

You can manually trigger maintenance:

```bash
curl -X POST https://api.easyexcel.in/api/subscriptions/maintenance
```

Response:
```json
{
  "status": "success",
  "tokens_refreshed": 5,
  "users_downgraded": 2
}
```

## How It Works

### Token Refresh Process
1. Finds all Free plan subscriptions created 30+ days ago
2. Resets `tokens_used` to 0
3. Updates `created_at` to current time (resets 30-day cycle)
4. Logs the action

### Downgrade Process
1. Finds all active Pro/Starter subscriptions
2. Checks if subscription expired (30+ days old or past `expires_at`)
3. Updates user plan to "Free"
4. Marks old subscription as "expired" or "cancelled"
5. Creates new Free subscription with reset tokens
6. Logs the action

### Webhook Handling
- PayPal sends webhook events to `/api/payments/webhook`
- Payment failures trigger `handle_payment_failure()`
- User is immediately downgraded to Free
- New Free subscription is created with reset tokens

## Monitoring

Check logs to see maintenance activity:

```bash
# View maintenance logs
tail -f /var/log/easyexcel-maintenance.log

# Or check application logs
# (depends on your deployment platform)
```

## Security

The maintenance endpoint should be:
- ✅ Called only by scheduled tasks (not publicly accessible)
- ✅ Protected with authentication if exposed publicly
- ✅ Rate-limited to prevent abuse

**Optional:** Add authentication to the endpoint:

```python
@app.post("/api/subscriptions/maintenance")
async def run_subscription_maintenance(
    auth_token: str = Header(..., alias="X-Maintenance-Token")
):
    if auth_token != os.getenv("MAINTENANCE_TOKEN"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ... rest of the code
```

Then set `MAINTENANCE_TOKEN` in your environment and use it in cron:

```bash
curl -X POST https://api.easyexcel.in/api/subscriptions/maintenance \
  -H "X-Maintenance-Token: your-secret-token"
```

## Troubleshooting

### Maintenance not running
- Check cron job is active: `crontab -l`
- Check cron logs: `grep CRON /var/log/syslog`
- Test endpoint manually: `curl -X POST https://api.easyexcel.in/api/subscriptions/maintenance`

### Users not being downgraded
- Check webhook is receiving events
- Verify subscription expiration dates in database
- Check application logs for errors

### Tokens not refreshing
- Verify subscriptions have correct `created_at` dates
- Check that subscriptions are marked as "active"
- Ensure maintenance endpoint is being called

## Database Schema

The maintenance relies on these fields:
- `subscriptions.created_at` - Used to determine 30-day cycle
- `subscriptions.expires_at` - Used to check expiration
- `subscriptions.status` - Must be "active" for maintenance
- `subscriptions.plan_name` - Determines which plan user has
- `subscriptions.tokens_used` - Reset to 0 on refresh

