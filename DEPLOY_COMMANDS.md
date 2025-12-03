# Deployment Commands - Quick Reference

## ⚠️ If Git Pull Fails (TLS/Connection Errors)

**Quick Fix:**
```bash
# Fix DNS first
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf
sudo chattr +i /etc/resolv.conf 2>/dev/null || true

# Make deploy.sh executable
cd /opt/easyexcel-backend
chmod +x deploy.sh

# Retry
git pull origin main
```

## 🚀 Standard Deployment (Most Common)

### Step 1: Connect to Droplet
```powershell
# From Windows PowerShell
ssh root@165.227.29.127
```

### Step 2: Deploy (After SSH connection)
```bash
cd /opt/easyexcel-backend
git pull origin main
systemctl restart easyexcel-backend
systemctl status easyexcel-backend
```

## 📋 One-Line Deployment (Quick)

```bash
cd /opt/easyexcel-backend && git pull origin main && systemctl restart easyexcel-backend && systemctl status easyexcel-backend
```

## 🔄 Full Deployment (With Dependencies)

```bash
cd /opt/easyexcel-backend
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --quiet
systemctl restart easyexcel-backend
systemctl status easyexcel-backend
```

## 🎯 Using the Deployment Script (New - Recommended)

```bash
cd /opt/easyexcel-backend
git pull origin main
chmod +x deploy.sh
./deploy.sh
```

## 🔍 Check Service Status

```bash
# Check backend status
systemctl status easyexcel-backend

# Check if service is running
systemctl is-active easyexcel-backend

# View recent logs
journalctl -u easyexcel-backend -n 50 --no-pager
```

## 🌐 Restart Nginx (If Needed)

```bash
# Restart Nginx
sudo systemctl restart nginx

# Check Nginx status
sudo systemctl status nginx

# Test Nginx config
sudo nginx -t
```

## 🐛 Troubleshooting Commands

```bash
# Check if backend is listening on port 8000
netstat -tlnp | grep 8000

# Check Gunicorn workers
ps aux | grep gunicorn | grep -v grep

# View full service logs
journalctl -u easyexcel-backend -f

# Check disk space
df -h

# Check memory usage
free -h
```

## 📝 Previous Commands We Used

### Basic Restart
```bash
systemctl restart easyexcel-backend
```

### Pull and Restart
```bash
cd /opt/easyexcel-backend
git pull origin main
systemctl restart easyexcel-backend
```

### With Status Check
```bash
cd /opt/easyexcel-backend && git pull origin main && systemctl restart easyexcel-backend && systemctl status easyexcel-backend
```

### Full Update with Dependencies
```bash
cd /opt/easyexcel-backend
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --quiet
systemctl restart easyexcel-backend
sleep 5
systemctl status easyexcel-backend
```

## 🎯 Most Used Command (Copy This!)

```bash
cd /opt/easyexcel-backend && git pull origin main && systemctl restart easyexcel-backend && systemctl status easyexcel-backend
```

This single command:
1. Navigates to backend directory
2. Pulls latest code
3. Restarts the service
4. Shows service status

## 💡 Pro Tips

- Always check status after restart: `systemctl status easyexcel-backend`
- If service fails, check logs: `journalctl -u easyexcel-backend -n 100`
- For large deployments, use the `deploy.sh` script
- If Nginx changes are made, restart both: `systemctl restart nginx && systemctl restart easyexcel-backend`

