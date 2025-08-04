#!/bin/bash

# Rebuild nginx config without any shell escaping issues
# This approach writes each section separately to avoid heredoc problems

set -e

BASE_DIR="/mnt/storage/streamlit-server"
APPS_DIR="$BASE_DIR/apps"
NGINX_CONF="$BASE_DIR/nginx/conf.d/streamlit.conf"

echo "Rebuilding nginx configuration..."

# Create the file by writing each part separately
cat > "$NGINX_CONF" << 'HEADER_EOF'
server {
    listen 80;
    server_name _;
    charset utf-8;
    
    location = / {
        return 200 '<!DOCTYPE html>
<html>
<head>
    <title>Streamlit Apps Server</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { color: #ff4b4b; text-align: center; }
        .app-list { list-style: none; padding: 0; }
        .app-list li { margin: 10px 0; padding: 15px; background: #f0f2f6; border-radius: 4px; }
        .app-list a { text-decoration: none; color: #262730; font-weight: bold; }
        .app-list a:hover { color: #ff4b4b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Streamlit Apps Server</h1>
        <p>Available Applications:</p>
        <ul class="app-list">
HEADER_EOF

# Add app list items
for app_dir in "$APPS_DIR"/*; do
    if [ -d "$app_dir" ] && [ -f "$app_dir/app.py" ]; then
        app_name=$(basename "$app_dir")
        echo "            <li><a href=\"/$app_name/\">$app_name</a> - Streamlit application</li>" >> "$NGINX_CONF"
    fi
done

# Add middle section
cat >> "$NGINX_CONF" << 'MIDDLE_EOF'
        </ul>
        <p><small>Add new apps to /mnt/storage/streamlit-server/apps/ and run deploy script</small></p>
    </div>
</body>
</html>';
        add_header Content-Type "text/html; charset=utf-8";
    }
MIDDLE_EOF

# Add location blocks for each app
for app_dir in "$APPS_DIR"/*; do
    if [ -d "$app_dir" ] && [ -f "$app_dir/app.py" ]; then
        app_name=$(basename "$app_dir")
        
        # Write the location block directly using printf to avoid any escaping
        printf "\n    location /%s/ {\n" "$app_name" >> "$NGINX_CONF"
        printf "        proxy_pass http://%s:8501/;\n" "$app_name" >> "$NGINX_CONF"
        cat >> "$NGINX_CONF" << 'LOCATION_EOF'
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
LOCATION_EOF
        printf "        proxy_set_header X-Forwarded-Prefix /%s;\n" "$app_name" >> "$NGINX_CONF"
        printf "    }\n" >> "$NGINX_CONF"
    fi
done

# Close the server block
echo "}" >> "$NGINX_CONF"

echo "✅ Nginx config rebuilt successfully"
echo "🔍 Checking for escaped semicolons..."

if grep -q "\\\\;" "$NGINX_CONF"; then
    echo "❌ Found escaped semicolons! Fixing..."
    sed -i 's/\\\\;/;/g' "$NGINX_CONF"
    echo "✅ Fixed escaped semicolons"
else
    echo "✅ No escaped semicolons found"
fi

echo "📝 Final proxy_pass lines:"
grep "proxy_pass" "$NGINX_CONF"
