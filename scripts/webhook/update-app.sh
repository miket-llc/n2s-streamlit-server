#!/bin/bash

# Update and restart script for individual apps
# Usage: ./update-app.sh <app-name>

set -e

APP_NAME="$1"
BASE_DIR="/mnt/storage/streamlit-server"
APPS_DIR="$BASE_DIR/apps"

if [ -z "$APP_NAME" ]; then
    echo "Usage: $0 <app-name>"
    exit 1
fi

if [ ! -d "$APPS_DIR/$APP_NAME" ]; then
    echo "❌ App directory $APPS_DIR/$APP_NAME does not exist"
    exit 1
fi

echo "🔄 Updating app: $APP_NAME"

# Change to app directory and update code
cd "$APPS_DIR/$APP_NAME"

echo "📥 Pulling latest changes..."
# Use fetch + reset to avoid merge conflicts
git fetch origin || {
    echo "❌ Failed to fetch from origin"
    exit 1
}

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Reset to latest remote version
git reset --hard "origin/$CURRENT_BRANCH" || {
    echo "❌ Failed to reset to latest remote version"
    exit 1
}

echo "✅ Code updated successfully"

# Now restart the container
echo "🔄 Restarting container..."
cd "$BASE_DIR"

# Restart the specific container
docker-compose restart "$APP_NAME" || {
    echo "❌ Failed to restart container: $APP_NAME"
    exit 1
}

echo "✅ Update complete for $APP_NAME"

# Show latest commit
cd "$APPS_DIR/$APP_NAME"
LATEST_COMMIT=$(git log --oneline -1)
echo "📝 Now running: $LATEST_COMMIT"
