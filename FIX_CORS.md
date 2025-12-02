# Fix CORS Error

## Issue
Frontend at `https://www.easyexcel.in` cannot access backend at `https://api.easyexcel.in` due to CORS policy.

## Solution

The CORS configuration in `app.py` already includes the frontend domain. The backend service needs to be restarted to apply the changes.

## Commands to Fix

```bash
# SSH into the server
ssh root@165.227.29.127

# Restart the backend service
systemctl restart easyexcel-backend

# Check if it's running
systemctl status easyexcel-backend

# Check logs for any errors
journalctl -u easyexcel-backend -n 50
```

## Verify CORS Headers

After restarting, test the CORS headers:

```bash
curl -H "Origin: https://www.easyexcel.in" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://api.easyexcel.in/process-file \
     -v
```

You should see `Access-Control-Allow-Origin: https://www.easyexcel.in` in the response headers.

## If Still Not Working

1. Check if nginx is adding CORS headers (might conflict)
2. Verify the backend is actually running on port 8000
3. Check firewall rules
4. Verify the domain DNS is pointing correctly

