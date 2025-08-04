#!/bin/bash

# Generate nginx config without shell escaping issues
# Usage: ./generate-nginx-config.sh

set -e

BASE_DIR="/mnt/storage/streamlit-server"
APPS_DIR="$BASE_DIR/apps"
NGINX_CONF="$BASE_DIR/nginx/conf.d/streamlit.conf"
TEMPLATE_DIR="$BASE_DIR/scripts/templates"

echo "Generating nginx configuration..."

# Start with base template
cp "$TEMPLATE_DIR/nginx-app.conf.template" "/tmp/nginx-config-temp"

# Generate app list HTML
APP_LIST=""
APP_LOCATIONS=""

for app_dir in "$APPS_DIR"/*; do
    if [ -d "$app_dir" ] && [ -f "$app_dir/app.py" ]; then
        app_name=$(basename "$app_dir")
        
        # Add to app list HTML
        APP_LIST="$APP_LIST            <li><a href=\"/$app_name/\">$app_name</a> - Streamlit application</li>"$'\n'
        
        # Generate location block from template
        location_block=$(cat "$TEMPLATE_DIR/app-location.conf.template")
        location_block=${location_block//\{\{APP_NAME\}\}/$app_name}
        location_block=${location_block//\{\{APP_PORT\}\}/8501}
        
        APP_LOCATIONS="$APP_LOCATIONS"$'\n'"$location_block"$'\n'
    fi
done

# Replace placeholders - using a different approach to avoid escaping issues
python3 -c "
import sys
import re

# Read the template
with open('/tmp/nginx-config-temp', 'r') as f:
    content = f.read()

# Replace placeholders
app_list = '''$APP_LIST'''
app_locations = '''$APP_LOCATIONS'''

content = content.replace('{{APP_LIST}}', app_list.strip())
content = content.replace('{{APP_LOCATIONS}}', app_locations.strip())

# Write final config
with open('$NGINX_CONF', 'w') as f:
    f.write(content)

print('✅ Nginx config generated successfully')
"

# Clean up
rm -f /tmp/nginx-config-temp

echo "Config written to: $NGINX_CONF"
