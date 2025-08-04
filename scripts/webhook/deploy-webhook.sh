#!/bin/sh
# Webhook deployment endpoint
# Listens to GitHub webhook requests and triggers deployments

APP_NAME=$1
REPO_URL=$2
BRANCH=${3:-main}

if [ -z "$APP_NAME" ] || [ -z "$REPO_URL" ]; then
  echo "Usage: $0 <app_name> <repo_url> [branch]"
  exit 1
fi

# Log the deployment request
echo "Received webhook request for app $APP_NAME ($BRANCH) from $REPO_URL"
echo "Triggering deployment..."

# Invoke deployment using the git-deploy script
/mnt/storage/streamlit-server/scripts/deploy-methods/git-deploy.sh "$REPO_URL" "$APP_NAME" "$BRANCH"

