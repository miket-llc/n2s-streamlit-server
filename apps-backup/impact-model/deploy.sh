#!/bin/bash

# N2S Impact Model Deployment Script
# Deploy to motoko.hopto.org

set -e

SERVER="motoko.hopto.org"
PORT="2222"
REMOTE_USER="${USER}"  # Uses current username, can be overridden
APP_DIR="/home/${REMOTE_USER}/n2s-impact-model"
SERVICE_NAME="n2s-impact-model"

echo "🚀 Deploying N2S Impact Model to ${SERVER}:${PORT}"

# Function to run commands on remote server
run_remote() {
    ssh -p ${PORT} ${REMOTE_USER}@${SERVER} "$1"
}

# Function to copy files to remote server
copy_to_remote() {
    scp -P ${PORT} -r "$1" ${REMOTE_USER}@${SERVER}:"$2"
}

echo "📦 Preparing deployment package..."

# Create a temporary directory with files to deploy
TEMP_DIR=$(mktemp -d)
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='.git' --exclude='*.pyc' . ${TEMP_DIR}/

echo "📤 Copying files to server..."
run_remote "mkdir -p ${APP_DIR}"
copy_to_remote "${TEMP_DIR}/" "${APP_DIR}"

echo "🐍 Setting up Python environment on server..."
run_remote "cd ${APP_DIR} && python3 -m venv venv"
run_remote "cd ${APP_DIR} && source venv/bin/activate && pip install --upgrade pip"
run_remote "cd ${APP_DIR} && source venv/bin/activate && pip install -r requirements.txt"

echo "📋 Creating systemd service..."
cat > ${TEMP_DIR}/n2s-impact-model.service << EOF
[Unit]
Description=N2S Impact Model Streamlit App
After=network.target

[Service]
Type=simple
User=${REMOTE_USER}
WorkingDirectory=${APP_DIR}
Environment=PATH=${APP_DIR}/venv/bin
ExecStart=${APP_DIR}/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

copy_to_remote "${TEMP_DIR}/n2s-impact-model.service" "/tmp/"
run_remote "sudo mv /tmp/n2s-impact-model.service /etc/systemd/system/"
run_remote "sudo systemctl daemon-reload"
run_remote "sudo systemctl enable ${SERVICE_NAME}"

echo "🌐 Setting up Nginx reverse proxy..."
cat > ${TEMP_DIR}/n2s-impact-model.nginx << EOF
server {
    listen 80;
    server_name motoko.hopto.org;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
}
EOF

copy_to_remote "${TEMP_DIR}/n2s-impact-model.nginx" "/tmp/"
run_remote "sudo mv /tmp/n2s-impact-model.nginx /etc/nginx/sites-available/n2s-impact-model"

# Check if site is already enabled, if not enable it
if ! run_remote "test -L /etc/nginx/sites-enabled/n2s-impact-model"; then
    run_remote "sudo ln -s /etc/nginx/sites-available/n2s-impact-model /etc/nginx/sites-enabled/"
fi

echo "🔄 Starting services..."
run_remote "sudo systemctl restart ${SERVICE_NAME}"
run_remote "sudo nginx -t && sudo systemctl reload nginx"

echo "🧹 Cleaning up..."
rm -rf ${TEMP_DIR}

echo "✅ Deployment complete!"
echo ""
echo "🌐 Your app should be available at: http://motoko.hopto.org"
echo "📊 Direct Streamlit access: http://motoko.hopto.org:8501"
echo ""
echo "📝 Useful commands:"
echo "  Check service status: ssh -p ${PORT} ${REMOTE_USER}@${SERVER} 'sudo systemctl status ${SERVICE_NAME}'"
echo "  View service logs:    ssh -p ${PORT} ${REMOTE_USER}@${SERVER} 'sudo journalctl -f -u ${SERVICE_NAME}'"
echo "  Restart service:      ssh -p ${PORT} ${REMOTE_USER}@${SERVER} 'sudo systemctl restart ${SERVICE_NAME}'"
echo "  Update app:           ./deploy.sh" 