@echo off
REM EasyExcel Backend - Quick Start Script

echo ============================================================
echo EasyExcel Backend Server
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if Python is available
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo Creating .env file...
    copy env.example .env >nul 2>&1
    if not exist .env (
        echo Creating new .env file...
        (
            echo # Google Gemini API Configuration
            echo # Get your API key from: https://makersuite.google.com/app/apikey
            echo GEMINI_API_KEY=your_gemini_api_key_here
            echo.
            echo # Server Configuration
            echo PORT=8000
            echo HOST=0.0.0.0
            echo.
            echo # File Management
            echo MAX_FILE_SIZE=52428800  # 50MB in bytes
            echo CLEANUP_DAYS=7
        ) > .env
    )
    echo.
    echo WARNING: Please set your GEMINI_API_KEY in the .env file
    echo Get your key from: https://makersuite.google.com/app/apikey
    echo.
    pause
)

REM Start the server
echo Starting server...
echo.
echo Server will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.

py start_server.py

pause



