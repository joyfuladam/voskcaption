@echo off
REM Caption5 Application Update Script (Windows)
REM This script pulls the latest changes from the repository and updates the application

echo 🔄 Updating Caption5 Application...

REM Check if we're in a git repository
if not exist ".git" (
    echo ❌ Error: Not in a git repository. Please run this script from the caption5 directory.
    pause
    exit /b 1
)

REM Check if there are uncommitted changes
git status --porcelain >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Warning: You have uncommitted changes. Consider committing them first.
    echo    Current changes:
    git status --short
    echo.
    set /p "continue=Continue with update? (y/N): "
    if /i not "%continue%"=="y" (
        echo Update cancelled.
        pause
        exit /b 1
    )
)

REM Fetch the latest changes
echo 📥 Fetching latest changes...
git fetch origin

REM Check if there are updates available
for /f "tokens=*" %%i in ('git rev-parse HEAD') do set LOCAL=%%i
for /f "tokens=*" %%i in ('git rev-parse origin/main') do set REMOTE=%%i

if "%LOCAL%"=="%REMOTE%" (
    echo ✅ Application is already up to date!
    pause
    exit /b 0
)

echo 📦 Updates available. Pulling latest changes...

REM Pull the latest changes
git pull origin main
if %errorlevel% equ 0 (
    echo ✅ Update successful!
    
    REM Check if requirements.txt changed
    git diff --name-only HEAD~1 HEAD | findstr "requirements.txt" >nul
    if %errorlevel% equ 0 (
        echo 📋 Dependencies may have changed. Consider running: pip install -r requirements.txt
    )
    
    REM Check if main application file changed
    git diff --name-only HEAD~1 HEAD | findstr "captionStable.py" >nul
    if %errorlevel% equ 0 (
        echo 🔄 Main application updated. You may need to restart the application.
    )
    
    echo.
    echo 🎉 Update complete! Check the README.md for any additional setup steps.
) else (
    echo ❌ Update failed. Please check for conflicts and try again.
)

pause
