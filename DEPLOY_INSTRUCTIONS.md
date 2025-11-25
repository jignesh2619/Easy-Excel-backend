# Quick Deploy Instructions

## Step 1: Check where app.py is located on the Droplet

Run this command to see the directory structure:

```powershell
ssh root@165.227.29.127 "ls -la /opt/easyexcel-backend/"
```

Enter your root password when prompted.

This will show you if `app.py` is directly in `/opt/easyexcel-backend/` or in a subdirectory.

## Step 2: Copy app.py to the correct location

Based on what you see, use one of these commands:

**If app.py is directly in `/opt/easyexcel-backend/`:**
```powershell
cd "C:\Users\manda\excel bot\backend"
scp -o StrictHostKeyChecking=no app.py root@165.227.29.127:/opt/easyexcel-backend/app.py
```

**If the backend is in a subdirectory (or if the above doesn't work):**
```powershell
cd "C:\Users\manda\excel bot\backend"
scp -o StrictHostKeyChecking=no app.py root@165.227.29.127:/opt/easyexcel-backend/backend/app.py
```

**If neither path exists, create the directory first:**
```powershell
ssh root@165.227.29.127 "mkdir -p /opt/easyexcel-backend/backend"
scp -o StrictHostKeyChecking=no app.py root@165.227.29.127:/opt/easyexcel-backend/backend/app.py
```

## Step 3: Restart the backend service

```powershell
ssh root@165.227.29.127 "systemctl restart easyexcel-backend"
```

## Step 4: Verify it's running

```powershell
ssh root@165.227.29.127 "systemctl status easyexcel-backend"
```

