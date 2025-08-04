# GitHub Actions CI/CD Setup for Streamlit Server

This guide sets up automated deployment from your GitHub repositories to your Streamlit server.

## 🚀 Quick Setup

### 1. SSH Key Setup

Generate an SSH key pair for GitHub Actions to access your server:

```bash
# On your local machine or server
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-actions-streamlit
```

Add the public key to your server's authorized_keys:
```bash
cat ~/.ssh/github-actions-streamlit.pub >> ~/.ssh/authorized_keys
```

### 2. GitHub Repository Secrets

For **BOTH** repositories (`miket-llc/n2s-tmmi-tracker` and `miket-llc/n2s-impact-model`):

1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Add these Repository Secrets:

```
STREAMLIT_SERVER_HOST = your-server-ip-or-domain
STREAMLIT_SERVER_USER = mdt
STREAMLIT_SERVER_SSH_KEY = [paste the private key content from ~/.ssh/github-actions-streamlit]
```

### 3. Add GitHub Actions Workflows

#### For n2s-tmmi-tracker:
1. Create `.github/workflows/` directory in your repo
2. Add file `.github/workflows/deploy.yml` with content from:
   `/mnt/storage/streamlit-server/github-actions-templates/deploy-tmmi-tracker.yml`

#### For n2s-impact-model:
1. Create `.github/workflows/` directory in your repo
2. Add file `.github/workflows/deploy.yml` with content from:
   `/mnt/storage/streamlit-server/github-actions-templates/deploy-impact-model.yml`

## 🔄 How It Works

1. **Push to main branch** → GitHub Actions triggers
2. **Run tests** → Validate Python syntax and Streamlit import
3. **Deploy** → SSH into your server and run deployment script
4. **Access apps** at:
   - `http://your-server-ip/tmmi-tracker/`
   - `http://your-server-ip/impact-model/`

## 🛠️ Manual Deployment (Fallback)

If you need to deploy manually:

```bash
# For TMMI Tracker
./scripts/deploy-methods/git-deploy.sh https://github.com/miket-llc/n2s-tmmi-tracker.git tmmi-tracker main

# For Impact Model  
./scripts/deploy-methods/git-deploy.sh https://github.com/miket-llc/n2s-impact-model.git impact-model main
```

## 📋 Deployment Features

- ✅ **Automated testing** before deployment
- ✅ **Zero-downtime deployment** with Docker
- ✅ **Automatic nginx configuration** updates
- ✅ **Deployment logging** to `/mnt/storage/streamlit-server/logs/deploy.log`
- ✅ **Rollback capability** via Git
- ✅ **Branch-based deployment** (main branch only)

## 🔍 Monitoring

View deployment logs:
```bash
tail -f /mnt/storage/streamlit-server/logs/deploy.log
```

Check app status:
```bash
./scripts/manage-server.sh status
```

View app logs:
```bash
docker-compose logs tmmi-tracker
docker-compose logs impact-model
```

## 🚨 Troubleshooting

If deployment fails:
1. Check GitHub Actions logs in your repository
2. SSH into server and check deployment logs
3. Verify server connectivity and SSH key setup
4. Ensure apps have proper `requirements.txt` files

## 🔐 Security Notes

- SSH key is restricted to deployment operations only
- Deployments only happen on main branch pushes
- All secrets are encrypted in GitHub
- Server access is logged and monitored
