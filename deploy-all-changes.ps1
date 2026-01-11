# Deploy all recent changes to DigitalOcean Droplet
# This script copies all modified files to the Droplet and restarts the service

$DROPLET_IP = "165.227.29.127"
$DROPLET_USER = "root"
$BACKEND_BASE_PATH = "/opt/easyexcel-backend"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Deploying all changes to DigitalOcean Droplet" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# List of files to deploy (all modified files)
$filesToDeploy = @(
    "app.py",
    "services\python_executor.py",
    "services\action_plan_bot.py",
    "services\chart_builder.py",
    "services\cleaning\text.py"
)

Write-Host "Files to deploy:" -ForegroundColor Yellow
foreach ($file in $filesToDeploy) {
    Write-Host "  - $file" -ForegroundColor Cyan
}
Write-Host ""

# Check if files exist
$missingFiles = @()
foreach ($file in $filesToDeploy) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "ERROR: The following files are missing:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please run this script from the backend directory." -ForegroundColor Yellow
    exit 1
}

Write-Host "Step 1: Copying files to Droplet..." -ForegroundColor Yellow
Write-Host "Target directory: $BACKEND_BASE_PATH" -ForegroundColor Cyan
Write-Host "You will be prompted for the root password." -ForegroundColor Yellow
Write-Host ""

# Copy each file
$failedFiles = @()
foreach ($file in $filesToDeploy) {
    $targetPath = $file -replace '\\', '/'
    $fullTargetPath = "${BACKEND_BASE_PATH}/${targetPath}"
    
    Write-Host "Copying $file to $fullTargetPath..." -ForegroundColor Cyan
    
    # Ensure target directory exists on remote
    $targetDir = Split-Path -Path $fullTargetPath -Parent
    ssh -o StrictHostKeyChecking=no "${DROPLET_USER}@${DROPLET_IP}" "mkdir -p $targetDir" | Out-Null
    
    # Copy file
    scp -o StrictHostKeyChecking=no $file "${DROPLET_USER}@${DROPLET_IP}:${fullTargetPath}"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $file copied successfully" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed to copy $file" -ForegroundColor Red
        $failedFiles += $file
    }
}

if ($failedFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to copy the following files:" -ForegroundColor Red
    foreach ($file in $failedFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please check your SSH connection and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "All files copied successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Step 2: Restarting backend service..." -ForegroundColor Yellow
Write-Host "You will be prompted for the root password again." -ForegroundColor Yellow
Write-Host ""

# SSH and restart service
ssh -o StrictHostKeyChecking=no "${DROPLET_USER}@${DROPLET_IP}" "systemctl restart easyexcel-backend; sleep 2; systemctl status easyexcel-backend --no-pager -l"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "Deployment complete!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend service has been restarted with all changes." -ForegroundColor Green
    Write-Host ""
    Write-Host "Deployed files:" -ForegroundColor Yellow
    foreach ($file in $filesToDeploy) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "Changes included:" -ForegroundColor Yellow
    Write-Host "  - Fixed 're' variable scoping errors" -ForegroundColor Cyan
    Write-Host "  - Added text splitting instructions" -ForegroundColor Cyan
    Write-Host "  - Fixed chart generation for all data types" -ForegroundColor Cyan
    Write-Host "  - Improved phone number formatting" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERROR: Failed to restart service!" -ForegroundColor Red
    Write-Host "Please check the service status manually." -ForegroundColor Yellow
    exit 1
}


