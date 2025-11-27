# File Size Limit Fix - 413 Payload Too Large

## Issue
The error `413 Payload Too Large` occurs when uploading files larger than nginx's default limit (1MB).

## Solution Applied

### Nginx Configuration
Added to `/etc/nginx/sites-available/api.easyexcel.in`:
- `client_max_body_size 100M;` - Allows uploads up to 100MB
- Increased proxy timeouts for large file processing:
  - `proxy_read_timeout 300s;`
  - `proxy_connect_timeout 300s;`
  - `proxy_send_timeout 300s;`

### FastAPI
FastAPI doesn't have a default file size limit, so it will accept files up to the nginx limit.

## Current Limits

- **Maximum file size:** 100MB
- **Timeout:** 300 seconds (5 minutes) for processing

## To Increase Further

If you need larger files, edit `/etc/nginx/sites-available/api.easyexcel.in` and change:
```nginx
client_max_body_size 100M;  # Change to 200M, 500M, etc.
```

Then reload nginx:
```bash
nginx -t
systemctl reload nginx
```

## Status

✅ **Fixed:** Nginx now accepts files up to 100MB
✅ **Reloaded:** Configuration applied

Try uploading your file again!

