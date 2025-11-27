# Fix Nginx Config

The nginx config has syntax errors due to PowerShell variable expansion. The backend CORS is working correctly, but the nginx config needs to be fixed.

## Quick Fix (Run on Server)

SSH into your server and run:

```bash
ssh root@165.227.29.127
```

Then run this command to fix the config:

```bash
cat > /etc/nginx/sites-available/api.easyexcel.in << 'NGINXCONF'
server {
    server_name api.easyexcel.in;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/api.easyexcel.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.easyexcel.in/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = api.easyexcel.in) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name api.easyexcel.in;
    return 404;
}
NGINXCONF

nginx -t
systemctl reload nginx
```

## Current Status

✅ **Backend CORS:** Working correctly
✅ **API:** Accessible and healthy
✅ **Headers:** Being returned correctly
⚠️ **Nginx Config:** Has syntax errors but nginx is still running with cached config

## Why This Happened

PowerShell expands `$host` to `System.Management.Automation.Internal.Host.InternalHost` before the command reaches SSH, corrupting the nginx config file.

## Solution

Run the fix command above directly on the server (not through PowerShell) to restore the correct config.

