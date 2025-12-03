# Automated Deployment Script for DigitalOcean Droplet
# This script SSHs into the droplet and runs all deployment commands

$DROPLET_IP = "165.227.29.127"
$DROPLET_USER = "root"
$BACKEND_DIR = "/opt/easyexcel-backend"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "EasyExcel Backend - Automated Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Connecting to droplet: $DROPLET_USER@$DROPLET_IP" -ForegroundColor Yellow
Write-Host ""

# Commands to run on the droplet (single line to avoid line ending issues)
$commands = "cd $BACKEND_DIR && chmod +x deploy.sh && git pull origin main && systemctl restart easyexcel-backend && sleep 3 && systemctl status easyexcel-backend --no-pager -l | head -20"

# Execute commands via SSH
Write-Host "Executing deployment commands..." -ForegroundColor Green
Write-Host ""

ssh "$DROPLET_USER@$DROPLET_IP" $commands

Write-Host ""
Write-Host "Deployment script completed!" -ForegroundColor Green

