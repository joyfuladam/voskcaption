#!/bin/bash

# Caption4 App Launcher for macOS
# Double-click this file to launch the application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set the terminal title
echo -e "\033]0;Caption4 App\007"

# Clear the terminal
clear

echo "🚀 Caption4 App Launcher"
echo "=========================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please ensure you have run the setup first."
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    echo "   Please install Python 3.8+ first."
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment!"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Check if the main app file exists
if [ ! -f "captionStable.py" ]; then
    echo "❌ Main application file 'captionStable.py' not found!"
    echo ""
    echo "Press any key to exit..."
    read -n 1
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

echo ""
echo "🌐 Local IP Address: $LOCAL_IP"
echo "🔗 Dashboard: http://$LOCAL_IP:8000"
echo "🔗 User View: http://$LOCAL_IP:8000/user"
echo "🔗 Production View: http://$LOCAL_IP:8000/"
echo ""
echo "📱 Starting Caption4 App..."
echo "⏹️  Press Ctrl+C to stop the application"
echo ""
echo "=========================="
echo ""

# Check if port 8000 is available, if not find an available port
PORT=8000
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "⚠️  Port $PORT is already in use. Finding available port..."
    
    # Find next available port
    for p in $(seq 8001 8010); do
        if ! lsof -ti:$p > /dev/null 2>&1; then
            PORT=$p
            echo "✅ Found available port: $PORT"
            break
        fi
    done
    
    if [ $PORT -eq 8000 ]; then
        echo "❌ No available ports found in range 8000-8010"
        echo "   Please stop other services using these ports first."
        echo ""
        echo "Press any key to exit..."
        read -n 1
        exit 1
    fi
else
    echo "✅ Port $PORT is available"
fi

# Set the port as an environment variable for the Python app
export CAPTION_PORT=$PORT

echo "🚀 Launching Caption4 App on port $PORT..."
echo ""

# Start the application
python3 captionStable.py

# If we get here, the app has stopped
echo ""
echo "🛑 Caption4 App has stopped."
deactivate
echo "✅ Virtual environment deactivated."
echo ""
echo "Press any key to exit..."
read -n 1
