#!/bin/bash

# N2S Streamlit Server Installation Script
# Usage: ./install-server.sh [install_path]

set -e

INSTALL_PATH="${1:-/mnt/storage/streamlit-server}"
REPO_URL="https://github.com/miket-llc/n2s-streamlit-server.git"

echo "🚀 Installing N2S Streamlit Server Platform"
echo "📁 Installation path: $INSTALL_PATH"
echo "📦 Repository: $REPO_URL"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please do not run this script as root"
    exit 1
fi

# Check for required commands
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Please install Docker first."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Please install Docker Compose first."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ Git is required but not installed. Please install Git first."; exit 1; }

echo "✅ Prerequisites check passed"

# Create installation directory
sudo mkdir -p "$(dirname "$INSTALL_PATH")"
sudo chown "$USER:$USER" "$(dirname "$INSTALL_PATH")"

# Clone or update repository
if [ -d "$INSTALL_PATH" ]; then
    echo "📥 Updating existing installation..."
    cd "$INSTALL_PATH"
    git pull origin main
else
    echo "📥 Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_PATH"
    cd "$INSTALL_PATH"
fi

# Set up directory permissions
echo "🔐 Setting up permissions..."
mkdir -p logs ssl apps
chmod +x scripts/*.sh
chmod +x scripts/*/*.sh
chmod +x deployment/server-setup/*.sh

# Create systemd service for auto-start
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/streamlit-server.service > /dev/null << SERVICE_EOF
[Unit]
Description=N2S Streamlit Server Platform
After=docker.service
Requires=docker.service

[Service]
Type=forking
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_PATH
ExecStart=$INSTALL_PATH/scripts/manage-server.sh start
ExecStop=$INSTALL_PATH/scripts/manage-server.sh stop
TimeoutStartSec=0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable streamlit-server

echo "🚀 Starting Streamlit server..."
./scripts/manage-server.sh start

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Verify installation
if ./scripts/manage-server.sh status | grep -q "Up"; then
    echo "✅ Installation successful!"
    echo ""
    echo "🌐 Server is running at:"
    echo "   http://$(hostname -I | awk '{print $1}')/"
    echo "   http://localhost/"
    echo ""
    echo "📋 Management commands:"
    echo "   Start:   $INSTALL_PATH/scripts/manage-server.sh start"
    echo "   Stop:    $INSTALL_PATH/scripts/manage-server.sh stop"
    echo "   Status:  $INSTALL_PATH/scripts/manage-server.sh status"
    echo "   Logs:    $INSTALL_PATH/scripts/manage-server.sh logs"
    echo ""
    echo "🔄 Auto-start on boot: systemctl status streamlit-server"
else
    echo "❌ Installation may have issues. Check logs:"
    echo "   $INSTALL_PATH/scripts/manage-server.sh logs"
    exit 1
fi
