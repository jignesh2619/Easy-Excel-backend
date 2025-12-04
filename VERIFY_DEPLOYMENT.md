# Verify Deployment Status

## Check if Service Restarted Successfully

```bash
ssh root@165.227.29.127 "systemctl status easyexcel-backend | head -15"
```

## Check Recent Logs

```bash
ssh root@165.227.29.127 "journalctl -u easyexcel-backend -n 20 --no-pager"
```

## Test Health Endpoint

```bash
ssh root@165.227.29.127 "curl -s http://localhost:8000/health"
```

## Verify Latest Code is Deployed

```bash
ssh root@165.227.29.127 "cd /opt/easyexcel-backend && git log -1 --oneline"
```

## Check if Token Optimization is Active

Look for the new lightweight prompt method in logs:
```bash
ssh root@165.227.29.127 "journalctl -u easyexcel-backend | grep -i 'lightweight\|token\|prompt' | tail -10"
```
