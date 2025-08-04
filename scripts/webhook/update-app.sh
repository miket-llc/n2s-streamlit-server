#!/bin/bash

# Script to update a specific app from GitHub
# Usage: ./update-app.sh <app-name>

set -e

APP_NAME="$1"
BASE_DIR="/mnt/storage/streamlit-server"
APPS_DIR="$BASE_DIR/apps"
DEPLOY_LOG="$BASE_DIR/logs/deploy.log"

if [ -z "$APP_NAME" ]; then
    echo "Usage: $0 <app-name>"
    exit 1
fi

if [ ! -d "$APPS_DIR/$APP_NAME" ]; then
    echo "❌ App directory $APPS_DIR/$APP_NAME does not exist"
    exit 1
fi

echo "🔄 Updating app: $APP_NAME"
echo "[$(date)] Updating $APP_NAME" >> "$DEPLOY_LOG"

cd "$APPS_DIR/$APP_NAME"

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Restart the container
echo "🔄 Restarting container..."
cd "$BASE_DIR"

# Map app names to service names in docker-compose
case "$APP_NAME" in
    "n2s-tmmi-tracker")
        SERVICE_NAME="n2s-tmmi-tracker"
        ;;
    "n2s-impact-model")
        SERVICE_NAME="n2s-impact-model"
        ;;
    *)
        SERVICE_NAME="$APP_NAME"
        ;;
esac

docker-compose restart "$SERVICE_NAME"

# Wait a bit for container to start
sleep 5

# Check if container is running
if docker-compose ps "$SERVICE_NAME" | grep -q "Up"; then
    echo "✅ Update successful!"
    echo "[$(date)] Successfully updated $APP_NAME" >> "$DEPLOY_LOG"
    
    # Show the latest commit info
    cd "$APPS_DIR/$APP_NAME"
    LATEST_COMMIT=$(git log --oneline -1)
    echo "📝 Latest commit: $LATEST_COMMIT"
else
    echo "❌ Update failed!"
    echo "[$(date)] Failed to update $APP_NAME" >> "$DEPLOY_LOG"
    
    # Show logs for debugging
    echo "Container logs:"
    docker-compose logs --tail=20 "$SERVICE_NAME"
    exit 1
fi
