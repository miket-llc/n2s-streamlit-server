#!/bin/bash

# Server Setup Script for N2S Impact Model
# Run this on motoko.hopto.org to prepare the server

set -e

echo "🔧 Setting up server for N2S Impact Model deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "📦 Installing system dependencies..."
sudo apt install -y python3 python3-venv python3-pip nginx systemctl

# Install Python development headers (needed for some packages)
sudo apt install -y python3-dev build-essential

# Ensure nginx is running and enabled
echo "🌐 Configuring Nginx..."
sudo systemctl enable nginx
sudo systemctl start nginx

# Configure firewall if ufw is available
if command -v ufw &> /dev/null; then
    echo "🔥 Configuring firewall..."
    sudo ufw allow ssh
    sudo ufw allow 'Nginx Full'
    sudo ufw --force enable
fi

# Create nginx configuration directory if it doesn't exist
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled

# Remove default nginx site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
fi

echo "✅ Server setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Run the deployment script from your local machine: ./deploy.sh"
echo "  2. Check that your domain motoko.hopto.org points to this server"
echo "  3. Consider setting up SSL/TLS with Let's Encrypt (optional)" 