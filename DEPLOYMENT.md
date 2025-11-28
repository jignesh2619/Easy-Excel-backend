# Deployment Guide

## Recent Changes to Deploy

### Major Updates:
1. ✅ **Two-Bot Architecture** - ActionPlanBot and ChartBot
2. ✅ **PythonExecutor** - Unified Python code execution
3. ✅ **ChartExecutor** - Chart generation executor
4. ✅ **Updated LLMAgent** - Routing between bots
5. ✅ **Updated ExcelProcessor** - Uses unified executors
6. ✅ **Removed old code** - Cleaned up legacy methods

### New Files:
- `services/action_plan_bot.py`
- `services/chart_bot.py`
- `services/python_executor.py`
- `services/chart_executor.py`

### Updated Files:
- `services/llm_agent.py`
- `services/excel_processor.py`
- `app.py`

## Deployment Command

Run this command on your DigitalOcean droplet:

```bash
cd /path/to/backend && git fetch origin main && git reset --hard origin/main && sudo systemctl restart excel-bot
```

Or if you need to SSH first:

```bash
ssh user@your-droplet-ip
cd /path/to/backend
git fetch origin main
git reset --hard origin/main
sudo systemctl restart excel-bot
```

## Alternative: If service name is different

If your service is named differently, check with:
```bash
sudo systemctl list-units | grep excel
```

Common service names:
- `excel-bot`
- `excel-bot.service`
- `easyexcel`
- `backend`

## Verify Deployment

After restarting, verify the service is running:

```bash
# Check service status
sudo systemctl status excel-bot

# Check if API is responding
curl http://localhost:8000/health

# Check logs
sudo journalctl -u excel-bot -f
```

## Rollback (if needed)

If something goes wrong, you can rollback to previous commit:

```bash
cd /path/to/backend
git log --oneline -5  # Find previous commit hash
git reset --hard <previous-commit-hash>
sudo systemctl restart excel-bot
```

## Pre-Deployment Checklist

- [ ] All changes committed and pushed to `origin/main`
- [ ] Tested locally (if possible)
- [ ] Backup current deployment (optional)
- [ ] SSH access to droplet ready
- [ ] Service name confirmed

## Post-Deployment Verification

1. ✅ Service starts without errors
2. ✅ Health endpoint responds
3. ✅ Test a simple request (e.g., "sum column A")
4. ✅ Test chart generation (e.g., "create bar chart")
5. ✅ Test conditional formatting (e.g., "highlight cells with X")
6. ✅ Test text replacement (e.g., "replace X with Y")

## Troubleshooting

### Service won't start:
```bash
# Check logs
sudo journalctl -u excel-bot -n 50

# Check for Python errors
cd /path/to/backend
python3 -m py_compile services/action_plan_bot.py
python3 -m py_compile services/chart_bot.py
python3 -m py_compile services/python_executor.py
python3 -m py_compile services/chart_executor.py
```

### Import errors:
```bash
# Verify all dependencies installed
pip3 install -r requirements.txt
```

### Port already in use:
```bash
# Check what's using port 8000
sudo lsof -i :8000
# Kill if needed
sudo kill -9 <PID>
```

