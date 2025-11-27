# 🚀 Backend Deployment Guide

## Quick Deploy (Already Set Up)

Your backend is **already deployed** on DigitalOcean! Here's how to update it:

## Method 1: Automatic Deploy (Recommended)

### Step 1: Pull Latest Code
```bash
ssh root@165.227.29.127
cd /opt/easyexcel-backend
git pull origin main
```

### Step 2: Install New Dependencies (if any)
```bash
cd /opt/easyexcel-backend
venv/bin/pip install -r requirements.txt
```

### Step 3: Restart Service
```bash
systemctl restart easyexcel-backend
```

### Step 4: Verify
```bash
systemctl status easyexcel-backend
curl http://localhost:8000/health
```

## Method 2: Manual Deploy (First Time Setup)

### Prerequisites
- DigitalOcean Droplet (1GB RAM recommended)
- SSH access to droplet
- Git repository access

### Step 1: Connect to Server
```bash
ssh root@165.227.29.127
```

### Step 2: Clone Repository
```bash
cd /opt
git clone https://github.com/jignesh2619/Easy-Excel-backend.git easyexcel-backend
cd easyexcel-backend
```

### Step 3: Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
```bash
nano .env
```

Add these variables:
```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_secret
PAYPAL_MODE=sandbox
PORT=8000
HOST=0.0.0.0
```

### Step 5: Create Systemd Service
```bash
sudo nano /etc/systemd/system/easyexcel-backend.service
```

Add this content:
```ini
[Unit]
Description=EasyExcel Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/easyexcel-backend
Environment="PATH=/opt/easyexcel-backend/venv/bin"
ExecStart=/opt/easyexcel-backend/start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 6: Create Start Script
```bash
nano /opt/easyexcel-backend/start.sh
```

Add this content:
```bash
#!/bin/bash
cd /opt/easyexcel-backend
source venv/bin/activate

# Load .env file
set -a
[ -f .env ] && . .env
set +a

# Export variables
export GEMINI_API_KEY
export SUPABASE_URL
export SUPABASE_KEY
export PAYPAL_CLIENT_ID
export PAYPAL_CLIENT_SECRET
export PAYPAL_MODE
export PORT
export HOST

# Start server
python start_server.py
```

Make it executable:
```bash
chmod +x /opt/easyexcel-backend/start.sh
```

### Step 7: Enable and Start Service
```bash
systemctl daemon-reload
systemctl enable easyexcel-backend
systemctl start easyexcel-backend
```

### Step 8: Verify Deployment
```bash
# Check service status
systemctl status easyexcel-backend

# Check logs
journalctl -u easyexcel-backend -f

# Test API
curl http://localhost:8000/health
```

## Updating Existing Deployment

### Quick Update
```bash
ssh root@165.227.29.127
cd /opt/easyexcel-backend
git pull origin main
venv/bin/pip install -r requirements.txt --quiet
systemctl restart easyexcel-backend
```

### With Verification
```bash
ssh root@165.227.29.127 << 'EOF'
cd /opt/easyexcel-backend
echo "Pulling latest code..."
git pull origin main
echo "Installing dependencies..."
venv/bin/pip install -r requirements.txt --quiet
echo "Restarting service..."
systemctl restart easyexcel-backend
sleep 5
echo "Checking status..."
systemctl status easyexcel-backend --no-pager | head -10
echo "Testing health endpoint..."
curl -s http://localhost:8000/health
EOF
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
journalctl -u easyexcel-backend -n 50

# Check if port is in use
netstat -tulpn | grep 8000

# Check Python
cd /opt/easyexcel-backend
venv/bin/python --version
```

### Dependencies Missing
```bash
cd /opt/easyexcel-backend
venv/bin/pip install -r requirements.txt
```

### Environment Variables Missing
```bash
cd /opt/easyexcel-backend
cat .env
# Make sure all required variables are set
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# Kill it if needed
kill -9 <PID>
```

## Current Server Info

- **IP:** 165.227.29.127
- **Location:** `/opt/easyexcel-backend`
- **Service:** `easyexcel-backend.service`
- **Port:** 8000
- **Status:** Running ✅

## Quick Commands Reference

```bash
# Restart service
systemctl restart easyexcel-backend

# Check status
systemctl status easyexcel-backend

# View logs
journalctl -u easyexcel-backend -f

# Stop service
systemctl stop easyexcel-backend

# Start service
systemctl start easyexcel-backend

# Pull latest code
cd /opt/easyexcel-backend && git pull origin main

# Install dependencies
cd /opt/easyexcel-backend && venv/bin/pip install -r requirements.txt
```

## Deployment Checklist

- [ ] Code pulled from GitHub
- [ ] Dependencies installed
- [ ] Environment variables configured
- [ ] Service restarted
- [ ] Health check passes
- [ ] Logs show no errors

## Need Help?

If deployment fails:
1. Check logs: `journalctl -u easyexcel-backend -n 100`
2. Verify environment: `cat /opt/easyexcel-backend/.env`
3. Test manually: `cd /opt/easyexcel-backend && venv/bin/python start_server.py`

