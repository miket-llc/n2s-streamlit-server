#!/bin/bash

# Professional Git-based deployment script
# Usage: ./git-deploy.sh <repo_url> [app_name] [branch]

set -e

REPO_URL="$1"
APP_NAME="$2"
BRANCH="${3:-main}"

BASE_DIR="/mnt/storage/streamlit-server"
APPS_DIR="$BASE_DIR/apps"
DEPLOY_LOG="$BASE_DIR/logs/deploy.log"

if [ -z "$REPO_URL" ]; then
    echo "Usage: $0 <repo_url> [app_name] [branch]"
    echo "Example: $0 https://github.com/user/my-streamlit-app.git my-app main"
    exit 1
fi

# Extract app name from repo URL if not provided
if [ -z "$APP_NAME" ]; then
    APP_NAME=$(basename "$REPO_URL" .git)
fi

# Ensure logs directory exists
mkdir -p "$BASE_DIR/logs"

echo "🚀 Starting deployment: $APP_NAME"
echo "📦 Repository: $REPO_URL"
echo "🌿 Branch: $BRANCH"
echo "📁 Target: $APPS_DIR/$APP_NAME"

# Log deployment
echo "[$(date)] Starting deployment of $APP_NAME from $REPO_URL" >> "$DEPLOY_LOG"

# Clone or update repository
if [ -d "$APPS_DIR/$APP_NAME" ]; then
    echo "📥 Updating existing repository..."
    cd "$APPS_DIR/$APP_NAME"
    git fetch origin
    git reset --hard "origin/$BRANCH"
    git clean -fd
else
    echo "📥 Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" "$APPS_DIR/$APP_NAME"
fi

cd "$APPS_DIR/$APP_NAME"

# Verify it's a Streamlit app
if [ ! -f "app.py" ] && [ ! -f "streamlit_app.py" ] && [ ! -f "main.py" ]; then
    echo "❌ Error: No Streamlit app file found (app.py, streamlit_app.py, or main.py)"
    exit 1
fi

# Determine the main file
MAIN_FILE="app.py"
if [ -f "streamlit_app.py" ]; then
    MAIN_FILE="streamlit_app.py"
elif [ -f "main.py" ] && [ ! -f "app.py" ]; then
    MAIN_FILE="main.py"
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "📝 Creating default requirements.txt..."
    cat > requirements.txt << REQ_EOF
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
REQ_EOF
fi

# Create secrets directory and template if not exists
mkdir -p .streamlit
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "🔐 Creating secrets.toml template..."
    sed "s/{{APP_NAME}}/$APP_NAME/g" "$BASE_DIR/scripts/templates/secrets.toml.template" > .streamlit/secrets.toml
fi

# Update docker-compose.yml
echo "🐳 Updating Docker configuration..."
cd "$BASE_DIR"

# Add to docker-compose if not exists
if ! grep -q "$APP_NAME:" docker-compose.yml; then
    echo "📝 Adding $APP_NAME to docker-compose.yml..."
    sed -i "/^networks:/i\\
  $APP_NAME:\\
    image: python:3.11-slim\\
    container_name: streamlit-$APP_NAME\\
    working_dir: /app\\
    volumes:\\
      - ./apps/$APP_NAME:/app\\
    command: >\\
      sh -c \"pip install -r requirements.txt &&\\
             streamlit run $MAIN_FILE --server.port=8501 --server.address=0.0.0.0 --server.headless=true\"\\
    networks:\\
      - streamlit-network\\
    restart: unless-stopped\\
    runtime: runc\\
    expose:\\
      - \"8501\"\\
" docker-compose.yml
fi

# Rebuild nginx configuration
echo "🌐 Updating nginx configuration..."
./scripts/rebuild-nginx-config.sh

# Deploy the app
echo "🚀 Deploying application..."
docker-compose up -d --build "$APP_NAME"

# Wait for container to be ready
echo "⏳ Waiting for container to be ready..."
sleep 10

# Verify deployment
if docker-compose ps "$APP_NAME" | grep -q "Up"; then
    echo "✅ Deployment successful!"
    echo "🌐 App available at: http://your-server-ip/$APP_NAME/"
    
    # Log successful deployment
    echo "[$(date)] Successfully deployed $APP_NAME" >> "$DEPLOY_LOG"
else
    echo "❌ Deployment failed!"
    echo "📋 Container logs:"
    docker-compose logs --tail=20 "$APP_NAME"
    
    # Log failed deployment
    echo "[$(date)] Failed to deploy $APP_NAME" >> "$DEPLOY_LOG"
    exit 1
fi

# Show final status
echo ""
echo "📊 Deployment Summary:"
echo "- App Name: $APP_NAME"
echo "- Repository: $REPO_URL"
echo "- Branch: $BRANCH"
echo "- Main File: $MAIN_FILE"
echo "- URL: http://your-server-ip/$APP_NAME/"
echo "- Logs: docker-compose logs $APP_NAME"
