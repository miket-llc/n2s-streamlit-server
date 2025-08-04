#!/bin/bash

# Remote deployment script for GitHub Actions
# This script is called by GitHub Actions to deploy apps

set -e

APP_NAME="$1"
REPO_URL="$2"
BRANCH="${3:-main}"

if [ -z "$APP_NAME" ] || [ -z "$REPO_URL" ]; then
    echo "Usage: $0 <app_name> <repo_url> [branch]"
    exit 1
fi

echo "🚀 Remote deployment triggered"
echo "App: $APP_NAME"
echo "Repo: $REPO_URL"
echo "Branch: $BRANCH"

# Navigate to streamlit server directory
cd /mnt/storage/streamlit-server

# Execute the git deployment
./scripts/deploy-methods/git-deploy.sh "$REPO_URL" "$APP_NAME" "$BRANCH"

echo "✅ Remote deployment completed"
