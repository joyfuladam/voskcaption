#!/bin/bash

# Caption5 Setup Script for New Computers
# Run this script on a new computer to set up Caption5

echo "🚀 Setting up Caption5 on this computer..."

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first:"
    echo "   macOS: brew install git (or download from git-scm.com)"
    echo "   Windows: Download from git-scm.com"
    echo "   Linux: sudo apt-get install git (Ubuntu/Debian) or sudo yum install git (CentOS/RHEL)"
    exit 1
fi

echo "✅ Git is installed"

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first:"
    echo "   macOS: brew install python3 (or download from python.org)"
    echo "   Windows: Download from python.org"
    echo "   Linux: sudo apt-get install python3 python3-pip (Ubuntu/Debian)"
    exit 1
fi

echo "✅ Python is installed"

# Determine Python command
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "📋 Using Python command: $PYTHON_CMD"

# Check if we're already in the caption directory
if [ -f "captionStable.py" ]; then
    echo "✅ Already in Caption5 directory"
else
    echo "📥 Cloning Caption5 repository..."
    
    # Clone the repository
    if git clone https://github.com/joyfuladam/caption.git; then
        echo "✅ Repository cloned successfully"
        cd caption
    else
        echo "❌ Failed to clone repository"
        exit 1
    fi
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Please check the repository."
    exit 1
fi

# Create virtual environment
echo "🐍 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment already exists"
else
    if $PYTHON_CMD -m venv venv; then
        echo "✅ Virtual environment created successfully"
    else
        echo "❌ Failed to create virtual environment. Trying alternative method..."
        if $PYTHON_CMD -m virtualenv venv; then
            echo "✅ Virtual environment created with virtualenv"
        else
            echo "❌ Failed to create virtual environment. Installing dependencies globally..."
            echo "⚠️  Note: This may conflict with other Python projects"
        fi
    fi
fi

# Activate virtual environment and install dependencies
if [ -d "venv" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
    
    echo "📦 Installing Python dependencies in virtual environment..."
    if pip install -r requirements.txt; then
        echo "✅ Dependencies installed successfully in virtual environment"
    else
        echo "⚠️  Some dependencies may have failed to install. You can try:"
        echo "   pip install --upgrade pip"
        echo "   pip install -r requirements.txt"
    fi
    
    # Deactivate virtual environment
    deactivate
else
    echo "📦 Installing Python dependencies globally..."
    if $PYTHON_CMD -m pip install -r requirements.txt; then
        echo "✅ Dependencies installed successfully globally"
    else
        echo "⚠️  Some dependencies may have failed to install. You can try:"
        echo "   $PYTHON_CMD -m pip install --user -r requirements.txt"
    fi
fi

# Set up configuration
echo "⚙️  Setting up configuration..."
if [ ! -f "config.json" ] && [ -f "config.template.json" ]; then
    echo "📋 Creating configuration file from template..."
    cp config.template.json config.json
    echo "✅ Configuration file created!"
    echo "⚠️  IMPORTANT: Edit config.json to add your Azure Speech API key"
else
    echo "✅ Configuration file already exists"
fi

# Create activation script
echo "📝 Creating activation script..."
cat > activate_caption5.sh << 'EOF'
#!/bin/bash
# Caption5 Virtual Environment Activation Script
echo "🔌 Activating Caption5 virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated!"
echo "🚀 You can now run: python captionStable.py"
echo "💡 To deactivate, run: deactivate"
EOF

chmod +x activate_caption5.sh

echo ""
echo "🎉 Caption5 setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit config.json to add your Azure Speech API key"
echo "   2. Activate virtual environment: source venv/bin/activate"
echo "   3. Run the application: python captionStable.py"
echo "   4. Or use the activation script: ./activate_caption5.sh"
echo "   5. For updates, use: ./update_app.sh"
echo "   6. Check README.md for more information"
echo ""
echo "💡 Quick start: ./activate_caption5.sh"
echo "🚀 Ready to start captioning!"
