# DigitalOcean Droplet Information

## Droplet Details

- **Name:** `ubuntu-s-1vcpu-512mb-10gb-sfo2-01`
- **IPv4 Address:** `165.227.29.127`
- **Private IP:** `10.120.0.2`
- **Specifications:** 2 GB Memory / 10 GB Disk / SFO2 - Ubuntu 24.04 (LTS) x64
- **Status:** ON

## Quick SSH Command

```bash
ssh root@165.227.29.127
```

Or from Windows PowerShell:
```powershell
ssh root@165.227.29.127
```

## Quick Deployment Commands

After SSH connection:

```bash
cd /opt/easyexcel-backend
git pull origin main
./deploy.sh
```

## Service Management

```bash
# Check backend status
systemctl status easyexcel-backend

# Restart backend
systemctl restart easyexcel-backend

# Check Nginx status
systemctl status nginx

# Restart Nginx
systemctl restart nginx
```

## API Endpoint

- **Backend API:** `https://api.easyexcel.in` (via Nginx)
- **Direct Backend:** `http://165.227.29.127:8000` (if needed for testing)

## Notes

- Droplet is located in San Francisco (SFO2) region
- Currently configured with 2 GB RAM and 1 CPU
- Backend service runs on port 8000
- Nginx proxies requests from port 80/443 to port 8000

