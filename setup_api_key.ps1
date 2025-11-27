# EasyExcel Backend - API Key Setup Script

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""
Write-Host "EasyExcel Backend - OpenAI API Key Setup" -ForegroundColor Green
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
$envFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    
    # Copy from env.example if it exists
    $exampleFile = Join-Path $PSScriptRoot "env.example"
    if (Test-Path $exampleFile) {
        Copy-Item $exampleFile $envFile
        Write-Host "✓ .env file created from template" -ForegroundColor Green
    } else {
        # Create new .env file
        @"
# OpenAI API Configuration
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration
PORT=8000
HOST=0.0.0.0

# File Management
MAX_FILE_SIZE=52428800  # 50MB in bytes
CLEANUP_DAYS=7
"@ | Out-File -FilePath $envFile -Encoding UTF8
        Write-Host "✓ .env file created" -ForegroundColor Green
    }
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "Instructions:" -ForegroundColor Yellow
Write-Host "1. Get your OpenAI API key from: " -NoNewline -ForegroundColor White
Write-Host "https://platform.openai.com/api-keys" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Open the .env file:" -ForegroundColor White
Write-Host "   $envFile" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Replace 'your_openai_api_key_here' with your actual API key" -ForegroundColor White
Write-Host ""
Write-Host "Example:" -ForegroundColor Yellow
Write-Host "   OPENAI_API_KEY=sk-...your-actual-key-here" -ForegroundColor Gray
Write-Host ""

# Check if API key is already set
$content = Get-Content $envFile -Raw
if ($content -match "OPENAI_API_KEY=your_openai_api_key_here" -or $content -match "OPENAI_API_KEY=$") {
    Write-Host "⚠️  API key not configured yet!" -ForegroundColor Red
    Write-Host ""
    
    $openFile = Read-Host "Would you like to open the .env file now? (Y/N)"
    if ($openFile -eq "Y" -or $openFile -eq "y") {
        notepad $envFile
    }
} else {
    Write-Host "✓ API key appears to be configured!" -ForegroundColor Green
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""







