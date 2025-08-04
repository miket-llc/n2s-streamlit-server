#!/bin/bash

# Container restart script for individual apps
# Usage: ./update-app.sh <app-name>

set -e

APP_NAME="$1"

if [ -z "$APP_NAME" ]; then
    echo "Usage: $0 <app-name>"
    exit 1
fi

echo "🔄 Restarting container for: $APP_NAME"

# The container name in docker-compose has a streamlit- prefix
CONTAINER_NAME="streamlit-$APP_NAME"

# Change to the streamlit-server directory
cd /mnt/storage/streamlit-server

# Restart the specific container
docker-compose restart "$APP_NAME" || {
    echo "❌ Failed to restart container: $APP_NAME"
    exit 1
}

echo "✅ Container $APP_NAME restarted successfully"
