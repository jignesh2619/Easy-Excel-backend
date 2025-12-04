# Deployment Troubleshooting: TLS Handshake Error

## Error
```
fatal: unable to access 'https://github.com/jignesh2619/Easy-Excel-backend.git/'
gnutls_handshake() failed: The TLS connection was non-properly terminated.
```

## Solutions

### Solution 1: Update Git and SSL Certificates (Recommended)

```bash
ssh root@165.227.29.127

# Update system packages
apt-get update
apt-get upgrade -y

# Update CA certificates
apt-get install --reinstall ca-certificates

# Update git
apt-get install --reinstall git

# Try pulling again
cd /opt/easyexcel-backend
git pull origin main
```

### Solution 2: Use SSH Instead of HTTPS (Best Long-term)

```bash
ssh root@165.227.29.127

# Check current remote URL
cd /opt/easyexcel-backend
git remote -v

# Change to SSH (if you have SSH keys set up)
git remote set-url origin git@github.com:jignesh2619/Easy-Excel-backend.git

# Or keep HTTPS but update git config
git config --global http.sslVerify true
git config --global http.postBuffer 524288000

# Try pulling again
git pull origin main
```

### Solution 3: Check System Time (Common Issue)

```bash
ssh root@165.227.29.127

# Check current time
date

# If time is wrong, sync with NTP
apt-get install ntpdate -y
ntpdate -s time.nist.gov

# Or use systemd-timesyncd
timedatectl set-ntp true
timedatectl status

# Try pulling again
cd /opt/easyexcel-backend
git pull origin main
```

### Solution 4: Temporary Workaround - Manual File Copy

If git pull continues to fail, you can manually update:

```bash
# On your local machine, create a zip of changes
cd backend
git archive -o backend-update.zip HEAD

# Copy to server
scp backend-update.zip root@165.227.29.127:/tmp/

# On server
ssh root@165.227.29.127
cd /opt/easyexcel-backend
unzip -o /tmp/backend-update.zip
systemctl restart easyexcel-backend
```

### Solution 5: Check Network Connectivity

```bash
ssh root@165.227.29.127

# Test GitHub connectivity
curl -I https://github.com
ping github.com

# Check DNS
nslookup github.com

# Check firewall
iptables -L -n | grep github
```

### Solution 6: Update Git Configuration

```bash
ssh root@165.227.29.127

cd /opt/easyexcel-backend

# Increase buffer size
git config --global http.postBuffer 524288000

# Set SSL backend
git config --global http.sslBackend openssl

# Or disable SSL verification (NOT RECOMMENDED, only for testing)
# git config --global http.sslVerify false

# Try pulling again
git pull origin main
```

## Quick Fix Command (Try This First)

```bash
ssh root@165.227.29.127 'cd /opt/easyexcel-backend && apt-get update -qq && apt-get install --reinstall -y ca-certificates git && git pull origin main && systemctl restart easyexcel-backend'
```

## Verify After Fix

```bash
ssh root@165.227.29.127 "cd /opt/easyexcel-backend && git log -1 --oneline && systemctl status easyexcel-backend | head -5"
```







