@echo off
REM Caption5 Setup Script for New Computers (Windows)
REM Run this script on a new Windows computer to set up Caption5

echo 🚀 Setting up Caption5 on this computer...

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed. Please install Git first:
    echo    Download from https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git is installed

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python is not installed. Please install Python 3.8+ first:
        echo    Download from https://python.org/downloads/
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

echo ✅ Python is installed
echo 📋 Using Python command: %PYTHON_CMD%

REM Check if we're already in the caption directory
if exist "captionStable.py" (
    echo ✅ Already in Caption5 directory
) else (
    echo 📥 Cloning Caption5 repository...
    
    REM Clone the repository
    git clone https://github.com/joyfuladam/caption.git
    if %errorlevel% equ 0 (
        echo ✅ Repository cloned successfully
        cd caption
    ) else (
        echo ❌ Failed to clone repository
        pause
        exit /b 1
    )
)

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found. Please check the repository.
    pause
    exit /b 1
)

echo 📦 Installing Python dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo ✅ Dependencies installed successfully
) else (
    echo ⚠️  Some dependencies may have failed to install. You can try:
    echo    %PYTHON_CMD% -m pip install --user -r requirements.txt
)

echo.
echo 🎉 Caption5 setup complete!
echo.
echo 📋 Next steps:
echo    1. Run the application: %PYTHON_CMD% captionStable.py
echo    2. For updates, use: update_app.bat
echo    3. Check README.md for more information
echo.
echo 🚀 Ready to start captioning!
pause
