#!/bin/bash

# User data script for automated server setup
set -e

exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "🚀 Starting N2S Streamlit Server installation..."

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    htop \
    vim

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install Docker Compose (standalone)
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Create installation directory
mkdir -p /opt/streamlit-server
chown ubuntu:ubuntu /opt/streamlit-server

# Clone repository as ubuntu user
sudo -u ubuntu git clone ${github_repo} /opt/streamlit-server

# Set up the server
cd /opt/streamlit-server
sudo -u ubuntu ./deployment/server-setup/docker-deploy.sh production

echo "✅ N2S Streamlit Server installation completed!"
echo "🌐 Server will be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)/"
