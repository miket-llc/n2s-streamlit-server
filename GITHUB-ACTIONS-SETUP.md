# GitHub Actions Setup for Auto-Deployment

This guide shows how to set up GitHub Actions in your Streamlit app repositories to automatically deploy to your server when you push code.

## 🔧 Setup Steps

### 1. Add GitHub Actions Workflow Files

#### For n2s-tmmi-tracker repository:

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Streamlit Server

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to Streamlit Server
      uses: appleboy/ssh-action@v1.0.3
      with:
        host: ${{ secrets.STREAMLIT_SERVER_HOST }}
        username: ${{ secrets.STREAMLIT_SERVER_USER }}
        key: ${{ secrets.STREAMLIT_SERVER_SSH_KEY }}
        script: |
          /mnt/storage/streamlit-server/scripts/webhook/update-app.sh n2s-tmmi-tracker
```

#### For n2s-impact-model repository:

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Streamlit Server

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to Streamlit Server
      uses: appleboy/ssh-action@v1.0.3
      with:
        host: ${{ secrets.STREAMLIT_SERVER_HOST }}
        username: ${{ secrets.STREAMLIT_SERVER_USER }}
        key: ${{ secrets.STREAMLIT_SERVER_SSH_KEY }}
        script: |
          /mnt/storage/streamlit-server/scripts/webhook/update-app.sh n2s-impact-model
```

### 2. Configure GitHub Secrets

For **BOTH** repositories, add these secrets in GitHub:

1. Go to repository → Settings → Secrets and variables → Actions
2. Add these Repository Secrets:

```
STREAMLIT_SERVER_HOST = your-server-ip-or-domain
STREAMLIT_SERVER_USER = mdt
STREAMLIT_SERVER_SSH_KEY = [paste your private SSH key content]
```

### 3. Generate SSH Key (if needed)

If you don't have an SSH key for GitHub Actions:

```bash
# Generate a new SSH key
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-actions-streamlit

# Add the public key to your server's authorized_keys
cat ~/.ssh/github-actions-streamlit.pub >> ~/.ssh/authorized_keys

# Use the private key content for STREAMLIT_SERVER_SSH_KEY secret
cat ~/.ssh/github-actions-streamlit
```

## 🚀 How It Works

1. **Push code** to main branch
2. **GitHub Actions triggers** the workflow
3. **SSH into server** using the provided credentials
4. **Run update script** which:
   - Pulls latest code from GitHub
   - Restarts the Docker container
   - Updates the running application

## ✅ Testing the Setup

### Manual Test

You can test the update mechanism manually:

```bash
# On your server
/mnt/storage/streamlit-server/scripts/webhook/update-app.sh n2s-tmmi-tracker
```

### GitHub Actions Test

1. Make a small change to your app
2. Commit and push to main branch
3. Check the Actions tab in GitHub to see the deployment
4. Verify the app updated on your server

## 📋 Troubleshooting

### Common Issues

**SSH Authentication Failed:**
- Verify the SSH key is correct
- Test SSH access manually: `ssh mdt@your-server-ip`
- Ensure the public key is in `~/.ssh/authorized_keys`

**Update Script Failed:**
- Check server logs: `tail -f /mnt/storage/streamlit-server/logs/deploy.log`
- Verify app directory exists and has correct git remote
- Check Docker container status: `docker-compose ps`

**Container Won't Start:**
- Check app logs: `docker-compose logs n2s-tmmi-tracker`
- Verify requirements.txt is valid
- Check for Python syntax errors

## 🔄 Current Status

The server is configured and ready. You just need to:

1. ✅ Server is running and configured
2. ⏳ Add workflow files to your repositories  
3. ⏳ Configure GitHub secrets
4. ✅ Test the deployment

Once steps 2-3 are complete, your apps will auto-deploy on every push to main!
