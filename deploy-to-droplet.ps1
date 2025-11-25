# Deploy backend app.py to DigitalOcean Droplet
# This script copies the updated app.py to the Droplet and restarts the service

$DROPLET_IP = "165.227.29.127"
$DROPLET_USER = "root"
$BACKEND_PATH = "/opt/easyexcel-backend/app.py"
$LOCAL_FILE = "app.py"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Deploying backend to DigitalOcean Droplet" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if app.py exists
if (-not (Test-Path $LOCAL_FILE)) {
    Write-Host "ERROR: $LOCAL_FILE not found in current directory!" -ForegroundColor Red
    Write-Host "Please run this script from the backend directory." -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Copying app.py to Droplet..." -ForegroundColor Yellow
Write-Host "Target: $BACKEND_PATH" -ForegroundColor Cyan
Write-Host "You will be prompted for the root password." -ForegroundColor Yellow
Write-Host ""

# Copy file using SCP
scp -o StrictHostKeyChecking=no $LOCAL_FILE "${DROPLET_USER}@${DROPLET_IP}:${BACKEND_PATH}"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "File copied successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Step 2: Restarting backend service..." -ForegroundColor Yellow
    Write-Host "You will be prompted for the root password again." -ForegroundColor Yellow
    Write-Host ""
    
    # SSH and restart service
    ssh -o StrictHostKeyChecking=no "${DROPLET_USER}@${DROPLET_IP}" "systemctl restart easyexcel-backend; systemctl status easyexcel-backend --no-pager -l"
    
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "Deployment complete!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend service has been restarted." -ForegroundColor Green
    Write-Host "The updated endpoint should now be available." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ERROR: Failed to copy file!" -ForegroundColor Red
    Write-Host "Please check your SSH connection and try again." -ForegroundColor Yellow
    exit 1
}
