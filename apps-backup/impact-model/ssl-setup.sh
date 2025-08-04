#!/bin/bash

# SSL Setup Script for N2S Impact Model
# Run this on the server to enable HTTPS with Let's Encrypt

set -e

SERVER_NAME="motoko.hopto.org"
EMAIL="your-email@example.com"  # Change this to your email

echo "🔒 Setting up SSL/HTTPS for ${SERVER_NAME}..."

# Install certbot
echo "📦 Installing Certbot..."
sudo apt update
sudo apt install -y snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

# Install certbot nginx plugin
sudo snap set certbot trust-plugin-with-root=ok
sudo snap install certbot-dns-cloudflare  # Optional: if using Cloudflare DNS

echo "📜 Obtaining SSL certificate..."
sudo certbot --nginx -d ${SERVER_NAME} --email ${EMAIL} --agree-tos --non-interactive

# Test automatic renewal
echo "🔄 Testing automatic renewal..."
sudo certbot renew --dry-run

echo "✅ SSL setup complete!"
echo ""
echo "🌐 Your app should now be available at: https://${SERVER_NAME}"
echo "🔒 SSL certificate will auto-renew via cron/systemd timer" 