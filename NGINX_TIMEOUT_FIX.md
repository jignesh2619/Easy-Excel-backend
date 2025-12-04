# Nginx Timeout Configuration Fix

## Problem
"Failed to fetch" errors occur because Nginx times out before the backend finishes processing large files.

## Solution
Update Nginx configuration to increase timeouts.

## Steps

1. **SSH into your droplet:**
   ```bash
   ssh root@your-droplet-ip
   ```

2. **Edit Nginx configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/easyexcel
   ```

3. **Update the location block** to include these timeout settings:
   ```nginx
   server {
       listen 80;
       server_name api.easyexcel.in;

       # Increase client body size for large file uploads
       client_max_body_size 100M;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_cache_bypass $http_upgrade;
           
           # Increase timeouts for large file processing (5 minutes)
           proxy_connect_timeout 300s;
           proxy_send_timeout 300s;
           proxy_read_timeout 300s;
           send_timeout 300s;
           
           # Increase buffer sizes
           proxy_buffer_size 128k;
           proxy_buffers 4 256k;
           proxy_busy_buffers_size 256k;
       }
   }
   ```

4. **Test the configuration:**
   ```bash
   sudo nginx -t
   ```

5. **If test passes, restart Nginx:**
   ```bash
   sudo systemctl restart nginx
   ```

6. **Verify Nginx is running:**
   ```bash
   sudo systemctl status nginx
   ```

## Verification

After making these changes:
- Large file uploads should no longer timeout
- The frontend will wait up to 5 minutes for responses
- Better error messages will be shown if timeouts still occur

## Notes

- The timeout is set to 300 seconds (5 minutes) which should be sufficient for most file processing
- If you need longer timeouts, increase all timeout values proportionally
- Make sure Gunicorn timeout (in `gunicorn_config.py`) is also set to 300 seconds or higher






