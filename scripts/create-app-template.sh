#!/bin/bash

# Create new Streamlit app template
# Usage: ./create-app-template.sh <app-name>

APP_NAME="$1"
BASE_DIR="/mnt/storage/streamlit-server"
APPS_DIR="$BASE_DIR/apps"

if [ -z "$APP_NAME" ]; then
    echo "Usage: $0 <app-name>"
    echo "Example: $0 my-dashboard"
    exit 1
fi

if [ -d "$APPS_DIR/$APP_NAME" ]; then
    echo "Error: App directory $APPS_DIR/$APP_NAME already exists"
    exit 1
fi

echo "Creating app template: $APP_NAME"

mkdir -p "$APPS_DIR/$APP_NAME/.streamlit"

# Create basic app.py
cat > "$APPS_DIR/$APP_NAME/app.py" << EOL
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="$APP_NAME",
    page_icon="🎈",
    layout="wide"
)

st.title("🎈 $APP_NAME")
st.write("Welcome to your new Streamlit app!")

# Add your app content here
st.header("Getting Started")
st.write("""
This is a template for your new Streamlit app. You can:

1. Edit this file to add your content
2. Add additional Python files as needed
3. Update requirements.txt with your dependencies
4. Deploy using: ../scripts/deploy-app.sh $APP_NAME
""")

# Sample interactive widget
name = st.text_input("Enter your name:")
if name:
    st.write(f"Hello, {name}! 👋")

# Sample chart
if st.button("Generate Sample Data"):
    data = pd.DataFrame({
        'x': range(50),
        'y': np.random.randn(50).cumsum()
    })
    st.line_chart(data.set_index('x'))

# Footer with secrets info
st.markdown("---")
st.markdown("**App Info:**")
try:
    st.write(f"App: {st.secrets.general.app_name}")
    st.write(f"Environment: {st.secrets.general.environment}")
except:
    st.write("Secrets not configured")
EOL

# Create requirements.txt
cat > "$APPS_DIR/$APP_NAME/requirements.txt" << EOL
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
EOL

# Create secrets.toml from template
sed "s/{{APP_NAME}}/$APP_NAME/g" "$BASE_DIR/scripts/templates/secrets.toml.template" > "$APPS_DIR/$APP_NAME/.streamlit/secrets.toml"

# Create README
cat > "$APPS_DIR/$APP_NAME/README.md" << EOL
# $APP_NAME

## Description
Add your app description here.

## Installation
This app is managed by the Streamlit server. Dependencies are listed in \`requirements.txt\`.

## Configuration
- Edit \`.streamlit/secrets.toml\` to configure app-specific settings
- Add any required API keys or database credentials to secrets.toml

## Deployment
To deploy this app:
\`\`\`bash
cd /mnt/storage/streamlit-server
./scripts/deploy-app.sh $APP_NAME
\`\`\`

## Access
Once deployed, access at: http://your-server/$APP_NAME/

## Files
- \`app.py\`: Main Streamlit application
- \`requirements.txt\`: Python dependencies
- \`.streamlit/secrets.toml\`: Configuration and secrets
- \`README.md\`: This documentation
EOL

echo "✅ App template created at: $APPS_DIR/$APP_NAME"
echo ""
echo "Files created:"
echo "- $APPS_DIR/$APP_NAME/app.py"
echo "- $APPS_DIR/$APP_NAME/requirements.txt"
echo "- $APPS_DIR/$APP_NAME/.streamlit/secrets.toml"
echo "- $APPS_DIR/$APP_NAME/README.md"
echo ""
echo "Next steps:"
echo "1. Edit $APPS_DIR/$APP_NAME/app.py"
echo "2. Update $APPS_DIR/$APP_NAME/requirements.txt if needed"
echo "3. Configure $APPS_DIR/$APP_NAME/.streamlit/secrets.toml"
echo "4. Deploy with: $BASE_DIR/scripts/deploy-app.sh $APP_NAME"
