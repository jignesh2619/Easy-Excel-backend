#!/bin/bash
# Script to restart backend server on DigitalOcean Droplet

echo "🔄 Restarting EasyExcel Backend..."

# SSH into droplet and restart service
ssh root@165.227.29.127 << 'EOF'
    echo "Connected to server..."
    cd /opt/easyexcel-backend || cd ~/easyexcel-backend
    
    # Pull latest code
    echo "📥 Pulling latest code..."
    git pull origin main
    
    # Restart systemd service (if running as service)
    if systemctl is-active --quiet easyexcel-backend; then
        echo "🔄 Restarting systemd service..."
        sudo systemctl restart easyexcel-backend
        sudo systemctl status easyexcel-backend
    else
        # If running manually, kill and restart
        echo "🔄 Restarting manual process..."
        pkill -f "python.*app.py" || pkill -f "uvicorn"
        sleep 2
        nohup python3 start_server.py > server.log 2>&1 &
        echo "✅ Server restarted. Check server.log for output."
    fi
    
    echo "✅ Backend restart complete!"
EOF

echo "✅ Done!"

