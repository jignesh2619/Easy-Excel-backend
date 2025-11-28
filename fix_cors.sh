#!/bin/bash
# Quick CORS fix script for EasyExcel backend

echo "🔍 Checking Nginx configuration..."

# Check if Nginx is installed and running
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
    
    # Find Nginx config file
    CONFIG_FILE="/etc/nginx/sites-available/default"
    if [ ! -f "$CONFIG_FILE" ]; then
        CONFIG_FILE="/etc/nginx/nginx.conf"
    fi
    
    if [ -f "$CONFIG_FILE" ]; then
        echo "📝 Found Nginx config: $CONFIG_FILE"
        echo "⚠️  Please manually edit this file to add CORS headers"
        echo "   See NGINX_CORS_SETUP.md for instructions"
    else
        echo "⚠️  Could not find Nginx config file"
    fi
else
    echo "ℹ️  Nginx is not running - backend is likely directly exposed"
    echo "✅ FastAPI CORS middleware should handle it"
fi

echo ""
echo "🔄 Restarting backend service..."
cd /opt/easyexcel-backend
git pull origin main
sudo systemctl restart easyexcel-backend.service

echo ""
echo "✅ Backend restarted. Check status with:"
echo "   sudo systemctl status easyexcel-backend.service"

