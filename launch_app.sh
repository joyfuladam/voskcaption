#!/bin/bash

# Launch script for Caption4 App
# This script activates the virtual environment and starts the application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Caption4 App..."
echo "📁 Working directory: $SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    echo "   Expected location: $SCRIPT_DIR/venv"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+ first."
    exit 1
fi

# Check if requirements are installed
if [ ! -f "venv/lib/python*/site-packages/fastapi" ]; then
    echo "⚠️  Dependencies not found in virtual environment."
    echo "   Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies."
        exit 1
    fi
    echo "✅ Dependencies installed successfully."
else
    echo "✅ Dependencies found in virtual environment."
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment."
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Check if the main app file exists
if [ ! -f "captionStable.py" ]; then
    echo "❌ Main application file 'captionStable.py' not found."
    exit 1
fi

# Get local IP address for display
LOCAL_IP=$(python3 -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
    s.close()
    print(ip)
except:
    print('127.0.0.1')
")

echo "🌐 Local IP Address: $LOCAL_IP"
echo "🔗 Dashboard will be available at: http://$LOCAL_IP:8000"
echo "🔗 User View will be available at: http://$LOCAL_IP:8000/user"
echo "🔗 Production View will be available at: http://$LOCAL_IP:8000/"
echo ""
echo "📱 Starting Caption4 App..."
echo "⏹️  Press Ctrl+C to stop the application"
echo ""

# Start the application
python3 captionStable.py

# If we get here, the app has stopped
echo ""
echo "🛑 Caption4 App has stopped."
deactivate
echo "✅ Virtual environment deactivated."

