#!/bin/bash

# Install GitHub monitor as a systemd service
# This provides secure, server-driven updates

set -e

SERVICE_NAME="github-repo-monitor"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
BASE_DIR="/mnt/storage/streamlit-server"

echo "🔧 Installing GitHub Repository Monitor..."

# Create systemd service
sudo tee "$SERVICE_FILE" > /dev/null << SERVICE_EOF
[Unit]
Description=GitHub Repository Monitor for Streamlit Apps
After=network-online.target docker.service
Wants=network-online.target
Requires=docker.service

[Service]
Type=simple
User=mdt
Group=mdt
WorkingDirectory=$BASE_DIR
ExecStart=/usr/bin/python3 $BASE_DIR/scripts/polling/github-monitor.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$BASE_DIR/logs $BASE_DIR/config $BASE_DIR/apps
PrivateTmp=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Create config directory and default config
sudo mkdir -p "$BASE_DIR/config"
sudo chown mdt:mdt "$BASE_DIR/config"

cat > "$BASE_DIR/config/monitor-config.json" << CONFIG_EOF
{
  "repositories": [
    {
      "name": "n2s-tmmi-tracker",
      "owner": "miket-llc", 
      "branch": "main",
      "path": "$BASE_DIR/apps/n2s-tmmi-tracker"
    },
    {
      "name": "n2s-impact-model",
      "owner": "miket-llc",
      "branch": "main", 
      "path": "$BASE_DIR/apps/n2s-impact-model"
    }
  ],
  "poll_interval": 300,
  "max_retries": 3
}
CONFIG_EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo "✅ GitHub monitor installed!"
echo ""
echo "🚀 Start with: sudo systemctl start $SERVICE_NAME"
echo "📊 Status:     sudo systemctl status $SERVICE_NAME"
echo "📋 Logs:       journalctl -u $SERVICE_NAME -f"
echo "🛑 Stop:       sudo systemctl stop $SERVICE_NAME"
echo ""
echo "Configuration: $BASE_DIR/config/monitor-config.json"
echo "Logs:          $BASE_DIR/logs/github-monitor.log"
