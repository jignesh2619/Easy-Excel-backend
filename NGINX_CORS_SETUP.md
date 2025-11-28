# Nginx CORS Configuration Guide

## Step 1: Find Your Nginx Configuration File

```bash
# Check if Nginx is installed
nginx -v

# Find your site configuration (usually one of these):
ls /etc/nginx/sites-available/
ls /etc/nginx/conf.d/

# Common locations:
# - /etc/nginx/sites-available/default
# - /etc/nginx/sites-available/easyexcel-api
# - /etc/nginx/nginx.conf
```

## Step 2: Edit the Nginx Configuration

```bash
# Edit the configuration file (replace with your actual file)
sudo nano /etc/nginx/sites-available/default
# OR
sudo nano /etc/nginx/nginx.conf
```

## Step 3: Add CORS Configuration

Find the `location` block for your API (usually `/` or `/api`) and add CORS headers:

```nginx
server {
    listen 80;
    server_name api.easyexcel.in;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' 'https://www.easyexcel.in' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
        add_header 'Access-Control-Allow-Headers' '*' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        
        # Handle OPTIONS preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://www.easyexcel.in' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
            add_header 'Access-Control-Allow-Headers' '*' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Content-Length' 0;
            add_header 'Content-Type' 'text/plain';
            return 204;
        }
    }
}
```

## Step 4: Test and Reload Nginx

```bash
# Test the configuration for syntax errors
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
# OR
sudo service nginx reload
```

## Step 5: Verify CORS is Working

```bash
# Test CORS headers
curl -H "Origin: https://www.easyexcel.in" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://api.easyexcel.in/process-file -v
```

You should see `Access-Control-Allow-Origin` in the response headers.

## Alternative: Quick Fix (If Nginx is Not Used)

If you're not using Nginx and the backend is directly exposed, the FastAPI CORS middleware should handle it. Just restart the service:

```bash
cd /opt/easyexcel-backend
git pull origin main
sudo systemctl restart easyexcel-backend.service
```

## Troubleshooting

1. **Check if Nginx is running:**
   ```bash
   sudo systemctl status nginx
   ```

2. **Check Nginx error logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Check if backend is running:**
   ```bash
   sudo systemctl status easyexcel-backend.service
   ```

4. **Check backend logs:**
   ```bash
   sudo journalctl -u easyexcel-backend.service -n 50
   ```

