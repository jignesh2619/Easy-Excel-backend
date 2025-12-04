# Fix Deployment Issues

## Issue 1: Git Pull Failing (TLS/Connection Errors)

### Symptoms:
- `gnutls_handshake() failed: The TLS connection was non-properly terminated`
- `Send failure: Broken pipe`

### Solution 1: Fix DNS (Most Common)
```bash
# Update DNS settings
sudo nano /etc/resolv.conf
```

Add these lines:
```
nameserver 8.8.8.8
nameserver 8.8.4.4
```

Make it permanent:
```bash
sudo chattr +i /etc/resolv.conf
sudo systemctl restart systemd-resolved
```

### Solution 2: Retry Git Pull
```bash
cd /opt/easyexcel-backend
git pull origin main
```

If still failing, try:
```bash
# Clear git cache
git config --global http.postBuffer 524288000
git pull origin main
```

### Solution 3: Use SSH Instead of HTTPS (If configured)
```bash
git remote set-url origin git@github.com:jignesh2619/Easy-Excel-backend.git
git pull origin main
```

## Issue 2: Permission Denied on deploy.sh

### Fix Permissions:
```bash
cd /opt/easyexcel-backend
chmod +x deploy.sh
./deploy.sh
```

## Quick Fix Commands (Run These)

```bash
# 1. Fix DNS
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf
sudo chattr +i /etc/resolv.conf 2>/dev/null || true

# 2. Make deploy.sh executable
cd /opt/easyexcel-backend
chmod +x deploy.sh

# 3. Retry git pull
git pull origin main

# 4. Deploy
./deploy.sh
```

## Alternative: Manual Deployment (If Git Still Fails)

```bash
cd /opt/easyexcel-backend
source venv/bin/activate
pip install -r requirements.txt --quiet
systemctl restart easyexcel-backend
systemctl status easyexcel-backend
```






