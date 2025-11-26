# 🔄 How to Restart Backend Server

## Option 1: If Running on DigitalOcean Droplet (Production)

### SSH and Restart:

```powershell
# Connect to your droplet
ssh root@165.227.29.127

# Once connected, run:
cd /opt/easyexcel-backend
git pull origin main
sudo systemctl restart easyexcel-backend
sudo systemctl status easyexcel-backend
```

### Or use the restart script:

```powershell
cd backend
bash scripts/restart_backend.sh
```

## Option 2: If Running Locally (Development)

### Stop current server:
- Press `Ctrl+C` in the terminal running the backend

### Start server:
```powershell
cd "C:\Users\manda\excel bot\backend"
py start_server.py
```

## Option 3: If Using Railway/Render/Other Platform

### Railway:
- Go to Railway dashboard
- Click "Redeploy" or "Restart"

### Render:
- Go to Render dashboard  
- Click "Manual Deploy" → "Deploy latest commit"

## Verify Restart

After restarting, check:
1. **Health endpoint**: https://api.easyexcel.in/health
2. **Check logs** for training data loading:
   ```
   Loaded X examples from dataset_realistic_500.xlsx
   Loaded X examples from dataset_multicategory_500.xlsx
   Loaded X examples from dataset_jsonheavy_500.xlsx
   Total training examples loaded: 1500
   ```

## What Happens on Restart

✅ Training data loads from `backend/data/` directory
✅ FeedbackLearner initializes
✅ TrainingDataLoader scans and loads all Excel files
✅ LLM Agent ready with 1,500 training examples
✅ System ready to process files with improved accuracy

