# EasyExcel Backend - Dependency Installation Script
# Run this script to install all required dependencies

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "EasyExcel Backend - Dependency Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for Python
Write-Host "Checking for Python..." -ForegroundColor Yellow
$pythonFound = $false
$pythonCmd = $null

# Try different Python commands
$pythonCommands = @("python", "python3", "py", "python.exe")

foreach ($cmd in $pythonCommands) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $version -match "Python") {
            Write-Host "✓ Python found: $version" -ForegroundColor Green
            $pythonCmd = $cmd
            $pythonFound = $true
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonFound) {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python first:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "2. During installation, check 'Add Python to PATH'" -ForegroundColor White
    Write-Host "3. Restart your terminal/PowerShell after installation" -ForegroundColor White
    Write-Host "4. Run this script again" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Get Python version
Write-Host ""
Write-Host "Python Version:" -ForegroundColor Yellow
& $pythonCmd --version
Write-Host ""

# Check if pip is available
Write-Host "Checking for pip..." -ForegroundColor Yellow
try {
    $pipVersion = & $pythonCmd -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0 -or $pipVersion -match "pip") {
        Write-Host "✓ pip found: $pipVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ pip not found. Installing pip..." -ForegroundColor Yellow
        Write-Host "Please install pip manually or reinstall Python with pip included" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ pip not found!" -ForegroundColor Red
    Write-Host "Please reinstall Python with pip included" -ForegroundColor Yellow
    exit 1
}

# Navigate to backend directory
$backendDir = Join-Path $PSScriptRoot "."
if (-not (Test-Path $backendDir)) {
    Write-Host "✗ Backend directory not found: $backendDir" -ForegroundColor Red
    exit 1
}

Set-Location $backendDir
Write-Host ""
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Upgrade pip first
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $pythonCmd -m pip install --upgrade pip --quiet
Write-Host "✓ pip upgraded" -ForegroundColor Green
Write-Host ""

# Install requirements
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

try {
    & $pythonCmd -m pip install -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✓ All dependencies installed successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Get your Gemini API key from: https://makersuite.google.com/app/apikey" -ForegroundColor White
        Write-Host "2. Create a .env file in the backend folder" -ForegroundColor White
        Write-Host "3. Add: GEMINI_API_KEY=your_api_key_here" -ForegroundColor White
        Write-Host "4. Run: python app.py" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "✗ Installation failed. Please check the errors above." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "✗ Error installing dependencies: $_" -ForegroundColor Red
    exit 1
}

Read-Host "Press Enter to exit"

