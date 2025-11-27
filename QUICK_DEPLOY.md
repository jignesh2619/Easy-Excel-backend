# ⚡ Quick Deploy Command

## One-Line Deploy (Fixed)

Use **single quotes** to avoid bash history expansion issues:

```bash
ssh root@165.227.29.127 'cd /opt/easyexcel-backend && git pull origin main && venv/bin/pip install -r requirements.txt --quiet && systemctl restart easyexcel-backend && echo "Deployed successfully"'
```

## Alternative (Without Special Characters)

```bash
ssh root@165.227.29.127 "cd /opt/easyexcel-backend && git pull origin main && venv/bin/pip install -r requirements.txt --quiet && systemctl restart easyexcel-backend && echo Deployed"
```

## Step-by-Step (If One-Line Fails)

```bash
# 1. Connect
ssh root@165.227.29.127

# 2. Pull code
cd /opt/easyexcel-backend
git pull origin main

# 3. Install dependencies
venv/bin/pip install -r requirements.txt

# 4. Restart
systemctl restart easyexcel-backend

# 5. Verify
systemctl status easyexcel-backend
curl http://localhost:8000/health
```

## Why the Error Happened

The `!` character in `'✅ Deployed!'` was interpreted by bash history expansion. Using single quotes prevents this.

## Quick Verify

```bash
ssh root@165.227.29.127 "systemctl status easyexcel-backend | head -10"
```

