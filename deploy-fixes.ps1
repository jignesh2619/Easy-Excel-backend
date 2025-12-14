# Deploy fixed service files to DigitalOcean Droplet
# This script copies the fixed Excel writer and processor files and restarts the service

$DROPLET_IP = "165.227.29.127"
$DROPLET_USER = "root"
$BACKEND_BASE_PATH = "/opt/easyexcel-backend"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Deploying Fixed Service Files" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Files to deploy
$filesToDeploy = @(
    @{
        Local = "services\excel_writer\write_xlsx.py"
        Remote = "$BACKEND_BASE_PATH/services/excel_writer/write_xlsx.py"
    },
    @{
        Local = "services\excel_processor.py"
        Remote = "$BACKEND_BASE_PATH/services/excel_processor.py"
    }
)

$allSuccess = $true

foreach ($file in $filesToDeploy) {
    $localFile = $file.Local
    $remotePath = $file.Remote
    
    Write-Host "Deploying: $localFile" -ForegroundColor Yellow
    Write-Host "Target: $remotePath" -ForegroundColor Cyan
    
    if (-not (Test-Path $localFile)) {
        Write-Host "ERROR: $localFile not found!" -ForegroundColor Red
        $allSuccess = $false
        continue
    }
    
    # Copy file using SCP
    scp -o StrictHostKeyChecking=no $localFile "${DROPLET_USER}@${DROPLET_IP}:${remotePath}"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] $localFile deployed successfully" -ForegroundColor Green
    } else {
        Write-Host "[FAILED] Failed to deploy $localFile" -ForegroundColor Red
        $allSuccess = $false
    }
    Write-Host ""
}

if ($allSuccess) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "All files deployed successfully!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Restarting backend service..." -ForegroundColor Yellow
    Write-Host "You will be prompted for the root password." -ForegroundColor Yellow
    Write-Host ""
    
    # SSH and restart service
    ssh -o StrictHostKeyChecking=no "${DROPLET_USER}@${DROPLET_IP}" "systemctl restart easyexcel-backend; systemctl status easyexcel-backend --no-pager -l"
    
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "Deployment complete!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend service has been restarted with fixes." -ForegroundColor Green
    Write-Host "Excel writing errors should now be resolved." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "Deployment failed!" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Some files failed to deploy. Please check the errors above." -ForegroundColor Yellow
    exit 1
}

