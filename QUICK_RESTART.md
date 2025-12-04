# Quick Restart Commands After Droplet Reboot

## Step 1: Check Backend Service Status
```bash
systemctl status easyexcel-backend
```

## Step 2: Restart Backend Service
```bash
systemctl restart easyexcel-backend
```

## Step 3: Check Status Again
```bash
systemctl status easyexcel-backend | head -15
```

## Step 4: Check Logs (if there are errors)
```bash
journalctl -u easyexcel-backend -n 30 --no-pager
```

## Step 5: Test Health Endpoint
```bash
curl http://localhost:8000/health
```

## Step 6: Restart Droplet Agent (for console access)
```bash
systemctl restart droplet-agent
systemctl status droplet-agent
```

## One-Line Command (All Steps)
```bash
systemctl restart easyexcel-backend && systemctl restart droplet-agent && systemctl status easyexcel-backend | head -15 && curl -s http://localhost:8000/health
```







