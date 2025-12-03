# Deployment Setup Complete ✅

## What Has Been Done

### ✅ Frontend Changes
- Added `fetchWithTimeout` wrapper with 5-minute timeout
- Improved error messages for timeout and connection failures
- Better user feedback for network issues

### ✅ Backend Changes
- Created `gunicorn_config.py` with 300s timeout
- Added GitHub Actions workflow for auto-deployment
- Created deployment scripts (`deploy.sh`, `webhook.sh`)
- Added Nginx timeout configuration guide

## Next Steps on Droplet

### 1. Update Gunicorn Config on Droplet

SSH into your droplet and copy the new config:

```bash
cd /opt/easyexcel-backend
git pull origin main
```

The `gunicorn_config.py` file is now in the repo. Make sure your systemd service uses it:

```bash
# Check if service is using the config file
cat /etc/systemd/system/easyexcel-backend.service | grep gunicorn_config
```

It should show:
```
ExecStart=/opt/easyexcel-backend/venv/bin/gunicorn -c /opt/easyexcel-backend/gunicorn_config.py app:app
```

If not, update the service file:
```bash
sudo nano /etc/systemd/system/easyexcel-backend.service
```

Update the ExecStart line to:
```
ExecStart=/opt/easyexcel-backend/venv/bin/gunicorn -c /opt/easyexcel-backend/gunicorn_config.py app:app
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart easyexcel-backend
```

### 2. Update Nginx Timeouts

Follow the instructions in `NGINX_TIMEOUT_FIX.md`:

```bash
sudo nano /etc/nginx/sites-available/easyexcel
```

Add these timeout settings to the `location /` block:
```nginx
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;
send_timeout 300s;
```

Test and restart:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Set Up Auto-Deployment

#### Option A: GitHub Actions (Recommended)

1. Go to your GitHub repository settings
2. Navigate to "Secrets and variables" → "Actions"
3. Add these secrets:
   - `DROPLET_IP`: Your droplet IP address
   - `DROPLET_USER`: Usually `root`
   - `DROPLET_SSH_KEY`: Your private SSH key (the entire key, including `-----BEGIN` and `-----END` lines)

4. The workflow will automatically deploy when you push to `main` branch

#### Option B: Manual Deployment Script

Make the deployment script executable:
```bash
chmod +x /opt/easyexcel-backend/deploy.sh
```

Then you can deploy manually with:
```bash
/opt/easyexcel-backend/deploy.sh
```

### 4. Verify Everything Works

1. **Check Gunicorn timeout:**
   ```bash
   cat /opt/easyexcel-backend/gunicorn_config.py | grep timeout
   ```
   Should show: `timeout = 300`

2. **Check service status:**
   ```bash
   systemctl status easyexcel-backend
   ```

3. **Check Nginx timeouts:**
   ```bash
   sudo nginx -T | grep timeout
   ```
   Should show the 300s timeouts

4. **Test a file upload** from the frontend to verify timeout errors are resolved

## Summary

✅ **Frontend**: Now has 5-minute timeout and better error messages  
✅ **Backend**: Gunicorn configured with 300s timeout  
✅ **Nginx**: Needs timeout update (follow `NGINX_TIMEOUT_FIX.md`)  
✅ **Auto-deployment**: GitHub Actions workflow ready (needs secrets configured)

## Troubleshooting

If you still see "Failed to fetch" errors:

1. **Check Nginx logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Check backend logs:**
   ```bash
   sudo journalctl -u easyexcel-backend -f
   ```

3. **Verify timeouts are set:**
   - Gunicorn: `cat gunicorn_config.py | grep timeout`
   - Nginx: `sudo nginx -T | grep timeout`

4. **Test backend directly:**
   ```bash
   curl -X GET http://localhost:8000/health
   ```

## Notes

- The timeout is set to 300 seconds (5 minutes) which should handle most file processing
- If you need longer timeouts, increase all timeout values proportionally
- Make sure Gunicorn timeout ≥ Nginx timeout
- Frontend timeout should be ≥ Nginx timeout

