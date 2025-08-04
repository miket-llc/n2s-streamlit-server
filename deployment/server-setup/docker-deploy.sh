#!/bin/bash

# Docker-based deployment for production servers
# Usage: ./docker-deploy.sh [environment]

set -e

ENVIRONMENT="${1:-production}"
PROJECT_NAME="n2s-streamlit-server"
INSTALL_PATH="/opt/streamlit-server"

echo "🚀 Deploying N2S Streamlit Server Platform"
echo "🏗️ Environment: $ENVIRONMENT"
echo "📁 Installation path: $INSTALL_PATH"

# Create deployment directory
sudo mkdir -p "$INSTALL_PATH"
sudo chown "$USER:$USER" "$INSTALL_PATH"

# Clone or update
if [ -d "$INSTALL_PATH/.git" ]; then
    echo "📥 Updating existing deployment..."
    cd "$INSTALL_PATH"
    git pull origin main
else
    echo "📥 Initial deployment..."
    git clone https://github.com/miket-llc/n2s-streamlit-server.git "$INSTALL_PATH"
    cd "$INSTALL_PATH"
fi

# Create production environment file
cat > .env << ENV_EOF
# N2S Streamlit Server Environment Configuration
ENVIRONMENT=$ENVIRONMENT
PROJECT_NAME=$PROJECT_NAME
COMPOSE_PROJECT_NAME=$PROJECT_NAME

# Server Configuration
SERVER_HOST=0.0.0.0
HTTP_PORT=80
HTTPS_PORT=443

# Docker Configuration
DOCKER_RESTART_POLICY=unless-stopped
DOCKER_LOG_DRIVER=json-file
DOCKER_LOG_MAX_SIZE=10m
DOCKER_LOG_MAX_FILE=3

# Security
SSL_ENABLED=false
ENV_EOF

# Set permissions
chmod +x scripts/*.sh scripts/*/*.sh deployment/server-setup/*.sh

# Deploy with Docker Compose
echo "🐳 Deploying with Docker Compose..."
docker-compose -f docker-compose.yml --env-file .env up -d --build

# Setup log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/streamlit-server > /dev/null << LOG_EOF
$INSTALL_PATH/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f $INSTALL_PATH/docker-compose.yml restart nginx || true
    endscript
}
LOG_EOF

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/streamlit-server.service > /dev/null << SERVICE_EOF
[Unit]
Description=N2S Streamlit Server Platform
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_PATH
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo systemctl daemon-reload
sudo systemctl enable streamlit-server

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Server endpoints:"
echo "   Main dashboard: http://$(hostname -I | awk '{print $1}')/"
echo "   Local access:   http://localhost/"
echo ""
echo "📋 Management:"
echo "   Status: sudo systemctl status streamlit-server"
echo "   Logs:   docker-compose logs -f"
echo "   Update: git pull && docker-compose up -d --build"
