#!/bin/bash

# Setup script to create desktop aliases for Caption4 App
# Run this script to create convenient aliases

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCH_SCRIPT="$SCRIPT_DIR/launch_app.command"

echo "🔧 Setting up Caption4 App desktop aliases..."
echo ""

# Check if launch script exists
if [ ! -f "$LAUNCH_SCRIPT" ]; then
    echo "❌ Launch script not found: $LAUNCH_SCRIPT"
    exit 1
fi

# Make sure it's executable
chmod +x "$LAUNCH_SCRIPT"

echo "✅ Launch script found and made executable: $LAUNCH_SCRIPT"
echo ""

# Create desktop alias
echo "📱 Creating desktop alias..."
echo "   You can now double-click 'launch_app.command' to launch the app"
echo ""

# Create a symbolic link on the desktop if possible
DESKTOP_DIR="$HOME/Desktop"
if [ -d "$DESKTOP_DIR" ]; then
    DESKTOP_LINK="$DESKTOP_DIR/Caption4 App"
    
    # Remove existing link if it exists
    if [ -L "$DESKTOP_LINK" ]; then
        rm "$DESKTOP_LINK"
        echo "🔄 Updated existing desktop link"
    fi
    
    # Create new link
    ln -s "$LAUNCH_SCRIPT" "$DESKTOP_LINK"
    echo "✅ Created desktop alias: $DESKTOP_LINK"
    echo "   Double-click 'Caption4 App' on your desktop to launch"
else
    echo "⚠️  Desktop directory not found, but you can still use the launch script directly"
fi

echo ""
echo "🚀 Setup complete! Here are your launch options:"
echo ""
echo "1. Double-click 'launch_app.command' in this folder"
echo "2. Double-click 'Caption4 App' on your desktop (if created)"
echo "3. Run from terminal: ./launch_app.sh"
echo "4. Create a custom alias in your shell profile:"
echo "   echo 'alias caption4=\"$LAUNCH_SCRIPT\"' >> ~/.zshrc"
echo "   source ~/.zshrc"
echo "   # Then just type: caption4"
echo ""
echo "📁 App location: $SCRIPT_DIR"
echo "🔗 Launch script: $LAUNCH_SCRIPT"

