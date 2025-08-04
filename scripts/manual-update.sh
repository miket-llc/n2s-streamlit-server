#!/bin/bash

# Manual update trigger for Streamlit apps
# Usage: ./manual-update.sh [app-name]

set -e

APP_NAME="$1"
BASE_DIR="/mnt/storage/streamlit-server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Manual Update Trigger${NC}"
echo "=========================="

if [ -z "$APP_NAME" ]; then
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 <app-name>           # Update specific app"  
    echo "  $0 all                  # Update all apps"
    echo ""
    echo -e "${YELLOW}Available apps:${NC}"
    for app_dir in "$BASE_DIR/apps"/*; do
        if [ -d "$app_dir" ] && [ -f "$app_dir/app.py" ]; then
            app=$(basename "$app_dir")
            echo "  - $app"
        fi
    done
    exit 1
fi

if [ "$APP_NAME" = "all" ]; then
    echo -e "${BLUE}🔄 Triggering update for all apps...${NC}"
    python3 "$BASE_DIR/scripts/polling/github-monitor.py" --once
else
    echo -e "${BLUE}🔄 Triggering update for: $APP_NAME${NC}"
    "$BASE_DIR/scripts/webhook/update-app.sh" "$APP_NAME"
fi

echo ""
echo -e "${GREEN}✅ Manual update complete!${NC}"
