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

REM Create virtual environment
echo 🐍 Creating virtual environment...
if exist "venv" (
    echo ✅ Virtual environment already exists
) else (
    %PYTHON_CMD% -m venv venv
    if %errorlevel% equ 0 (
        echo ✅ Virtual environment created successfully
    ) else (
        echo ❌ Failed to create virtual environment. Trying alternative method...
        %PYTHON_CMD% -m virtualenv venv
        if %errorlevel% equ 0 (
            echo ✅ Virtual environment created with virtualenv
        ) else (
            echo ❌ Failed to create virtual environment. Installing dependencies globally...
            echo ⚠️  Note: This may conflict with other Python projects
        )
    )
)

REM Activate virtual environment and install dependencies
if exist "venv" (
    echo 🔌 Activating virtual environment...
    call venv\Scripts\activate.bat
    
    echo 📦 Installing Python dependencies in virtual environment...
    pip install -r requirements.txt
    if %errorlevel% equ 0 (
        echo ✅ Dependencies installed successfully in virtual environment
    ) else (
        echo ⚠️  Some dependencies may have failed to install. You can try:
        echo    pip install --upgrade pip
        echo    pip install -r requirements.txt
    )
    
    REM Deactivate virtual environment
    deactivate
) else (
    echo 📦 Installing Python dependencies globally...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if %errorlevel% equ 0 (
        echo ✅ Dependencies installed successfully globally
    ) else (
        echo ⚠️  Some dependencies may have failed to install. You can try:
        echo    %PYTHON_CMD% -m pip install --user -r requirements.txt
    )
)

REM Set up configuration
echo ⚙️  Setting up configuration...
if not exist "config.json" (
    if exist "config.template.json" (
        echo 📋 Creating configuration file from template...
        copy config.template.json config.json
        echo ✅ Configuration file created!
        echo ⚠️  IMPORTANT: Edit config.json to add your Azure Speech API key
    ) else (
        echo ✅ Configuration file already exists
    )
) else (
    echo ✅ Configuration file already exists
)

REM Create activation script
echo 📝 Creating activation script...
echo @echo off > activate_caption5.bat
echo REM Caption5 Virtual Environment Activation Script >> activate_caption5.bat
echo echo 🔌 Activating Caption5 virtual environment... >> activate_caption5.bat
echo call venv\Scripts\activate.bat >> activate_caption5.bat
echo echo ✅ Virtual environment activated! >> activate_caption5.bat
echo echo 🚀 You can now run: python captionStable.py >> activate_caption5.bat
echo echo 💡 To deactivate, run: deactivate >> activate_caption5.bat
echo pause >> activate_caption5.bat

echo.
echo 🎉 Caption5 setup complete!
echo.
echo 📋 Next steps:
echo    1. Edit config.json to add your Azure Speech API key
echo    2. Activate virtual environment: venv\Scripts\activate.bat
echo    3. Run the application: python captionStable.py
echo    4. Or use the activation script: activate_caption5.bat
echo    5. For updates, use: update_app.bat
echo    6. Check README.md for more information
echo.
echo 💡 Quick start: activate_caption5.bat
echo 🚀 Ready to start captioning!
pause
