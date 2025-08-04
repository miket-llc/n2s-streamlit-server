#!/bin/bash

# Deploy new Streamlit app script (FIXED VERSION - no more escaped semicolons!)
# Usage: ./deploy-app.sh <app-name> [port]

set -e

APP_NAME="$1"
PORT="${2:-8501}"
BASE_DIR="/mnt/storage/streamlit-server"
APPS_DIR="$BASE_DIR/apps"
COMPOSE_FILE="$BASE_DIR/docker-compose.yml"

if [ -z "$APP_NAME" ]; then
    echo "Usage: $0 <app-name> [port]"
    echo "Example: $0 my-dashboard 8502"
    exit 1
fi

if [ ! -d "$APPS_DIR/$APP_NAME" ]; then
    echo "Error: App directory $APPS_DIR/$APP_NAME does not exist"
    echo "Please create the app directory and add your Streamlit app files"
    exit 1
fi

if [ ! -f "$APPS_DIR/$APP_NAME/app.py" ]; then
    echo "Error: No app.py found in $APPS_DIR/$APP_NAME"
    exit 1
fi

echo "Deploying Streamlit app: $APP_NAME"

# Add service to docker-compose.yml if it doesn't exist
if ! grep -q "$APP_NAME:" "$COMPOSE_FILE"; then
    echo "Adding $APP_NAME to docker-compose.yml..."
    
    # Insert before networks section
    sed -i "/^networks:/i\\
  $APP_NAME:\\
    image: python:3.11-slim\\
    container_name: streamlit-$APP_NAME\\
    working_dir: /app\\
    volumes:\\
      - ./apps/$APP_NAME:/app\\
    command: >\\
      sh -c \"pip install -r requirements.txt &&\\
             streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true\"\\
    networks:\\
      - streamlit-network\\
    restart: unless-stopped\\
    runtime: runc\\
    expose:\\
      - \"$PORT\"\\
" "$COMPOSE_FILE"
fi

# Rebuild nginx configuration using the robust method
echo "Rebuilding nginx configuration..."
"$BASE_DIR/scripts/rebuild-nginx-config.sh"

echo "Restarting services..."
cd "$BASE_DIR"
docker-compose up -d --build

echo "✅ App $APP_NAME deployed successfully!"
echo "🌐 Access it at: http://your-server-ip/$APP_NAME/"
echo ""
echo "To view logs: docker-compose logs $APP_NAME"
echo "To restart: docker-compose restart $APP_NAME"
