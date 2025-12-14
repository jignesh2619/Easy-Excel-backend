# Check backend logs via SSH to diagnose performance issues
# This script connects to the DigitalOcean Droplet and checks various log sources

$DROPLET_IP = "165.227.29.127"
$DROPLET_USER = "root"
$SERVICE_NAME = "easyexcel-backend"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Checking Backend Logs for Performance Issues" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Function to execute SSH command and display output
function Invoke-SSHCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "`n$Description" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    ssh -o StrictHostKeyChecking=no "${DROPLET_USER}@${DROPLET_IP}" $Command
    Write-Host ""
}

# 1. Check service status
Write-Host "1. Checking service status..." -ForegroundColor Cyan
Invoke-SSHCommand "systemctl status $SERVICE_NAME --no-pager -l" "Service Status"

# 2. Check recent logs (last 100 lines)
Write-Host "2. Checking recent logs (last 100 lines)..." -ForegroundColor Cyan
Invoke-SSHCommand "journalctl -u $SERVICE_NAME -n 100 --no-pager" "Recent Logs (Last 100 lines)"

# 3. Check logs for errors in the last hour
Write-Host "3. Checking errors in the last hour..." -ForegroundColor Cyan
Invoke-SSHCommand "journalctl -u $SERVICE_NAME --since '1 hour ago' --no-pager | grep -i 'error\|exception\|timeout\|failed\|slow'" "Errors in Last Hour"

# 4. Check logs for slow requests (look for high duration times)
Write-Host "4. Checking for slow requests (high duration)..." -ForegroundColor Cyan
Invoke-SSHCommand "journalctl -u $SERVICE_NAME --since '1 hour ago' --no-pager | grep -E 'D=[0-9]{6,}' | tail -20" "Slow Requests (Duration > 1 second)"

# 5. Check system resources
Write-Host "5. Checking system resources..." -ForegroundColor Cyan
Invoke-SSHCommand "echo 'CPU Usage:'; top -bn1 | grep 'Cpu(s)' | head -1; echo ''; echo 'Memory Usage:'; free -h; echo ''; echo 'Disk Usage:'; df -h /" "System Resources"

# 6. Check for timeout errors
Write-Host "6. Checking for timeout errors..." -ForegroundColor Cyan
Invoke-SSHCommand "journalctl -u $SERVICE_NAME --since '1 hour ago' --no-pager | grep -i 'timeout\|timed out\|504\|503'" "Timeout Errors"

# 7. Check process status and memory usage
Write-Host "7. Checking process status..." -ForegroundColor Cyan
Invoke-SSHCommand "ps aux | grep -E 'gunicorn|uvicorn|python.*app.py' | grep -v grep" "Process Status"

# 8. Check recent requests with response times
Write-Host "8. Checking recent requests with response times..." -ForegroundColor Cyan
Invoke-SSHCommand "journalctl -u $SERVICE_NAME --since '30 minutes ago' --no-pager | grep -E 'POST|GET|PUT|DELETE' | tail -30" "Recent API Requests"

# 9. Check for database/API connection issues
Write-Host "9. Checking for connection issues..." -ForegroundColor Cyan
Invoke-SSHCommand "journalctl -u $SERVICE_NAME --since '1 hour ago' --no-pager | grep -i 'connection\|connect\|database\|supabase\|api.*key'" "Connection Issues"

# 10. Check gunicorn worker status
Write-Host "10. Checking gunicorn worker status..." -ForegroundColor Cyan
Invoke-SSHCommand "ps aux | grep gunicorn | grep -v grep | wc -l; echo 'workers running'" "Gunicorn Workers"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Log check complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To view logs in real-time, run:" -ForegroundColor Yellow
Write-Host "  ssh ${DROPLET_USER}@${DROPLET_IP} 'journalctl -u $SERVICE_NAME -f'" -ForegroundColor Cyan
Write-Host ""


