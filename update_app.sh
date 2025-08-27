#!/bin/bash

# Caption5 Application Update Script
# This script pulls the latest changes from the repository and updates the application

echo "🔄 Updating Caption5 Application..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository. Please run this script from the caption5 directory."
    exit 1
fi

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes. Consider committing them first."
    echo "   Current changes:"
    git status --short
    echo ""
    read -p "Continue with update? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled."
        exit 1
    fi
fi

# Fetch the latest changes
echo "📥 Fetching latest changes..."
git fetch origin

# Check if there are updates available
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ Application is already up to date!"
    exit 0
fi

echo "📦 Updates available. Pulling latest changes..."

# Pull the latest changes
if git pull origin main; then
    echo "✅ Update successful!"
    
    # Check if requirements.txt changed
    if git diff --name-only HEAD~1 HEAD | grep -q "requirements.txt"; then
        echo "📋 Dependencies may have changed. Updating virtual environment..."
        
        # Check if virtual environment exists
        if [ -d "venv" ]; then
            echo "🔌 Activating virtual environment to update dependencies..."
            source venv/bin/activate
            
            if pip install -r requirements.txt; then
                echo "✅ Dependencies updated successfully in virtual environment"
            else
                echo "⚠️  Some dependencies may have failed to update. You can try:"
                echo "   source venv/bin/activate"
                echo "   pip install --upgrade pip"
                echo "   pip install -r requirements.txt"
            fi
            
            deactivate
        else
            echo "⚠️  Virtual environment not found. Consider running setup_new_computer.sh first"
            echo "   Or install dependencies manually: pip install -r requirements.txt"
        fi
    fi
    
    # Check if main application file changed
    if git diff --name-only HEAD~1 HEAD | grep -q "captionStable.py"; then
        echo "🔄 Main application updated. You may need to restart the application."
    fi
    
    # Check if virtual environment scripts were added
    if git diff --name-only HEAD~1 HEAD | grep -q "activate_caption5"; then
        echo "🐍 New virtual environment activation scripts added!"
        echo "   Use: ./activate_caption5.sh (macOS/Linux) or activate_caption5.bat (Windows)"
    fi
    
    echo ""
    echo "🎉 Update complete! Check the README.md for any additional setup steps."
    echo ""
    echo "💡 Quick start:"
    if [ -d "venv" ]; then
        echo "   source venv/bin/activate && python captionStable.py"
    else
        echo "   ./activate_caption5.sh (macOS/Linux) or activate_caption5.bat (Windows)"
    fi
else
    echo "❌ Update failed. Please check for conflicts and try again."
    exit 1
fi
