# Manual Update Triggers

## 🚀 Quick Manual Updates

### **Method 1: Management Script** ⭐ *Recommended*
```bash
# Update specific app
./scripts/manage-server.sh update n2s-tmmi-tracker
./scripts/manage-server.sh update n2s-impact-model

# Update all apps
./scripts/manage-server.sh update all
```

### **Method 2: Direct Script**
```bash
# Update specific app
./scripts/manual-update.sh n2s-tmmi-tracker
./scripts/manual-update.sh n2s-impact-model

# Update all apps  
./scripts/manual-update.sh all
```

### **Method 3: Quick Shortcut**
```bash
# Update specific app
./update-app n2s-tmmi-tracker

# Update all apps
./update-app all
```

### **Method 4: Monitor Script (All Apps)**
```bash
# Trigger full repository scan (all apps)
python3 scripts/polling/github-monitor.py --once
```

## 📋 **What Each Method Does:**

### **Single App Update:**
1. **Pulls latest code** from GitHub
2. **Restarts the container** with new code
3. **Shows latest commit** info
4. **Reports success/failure**

### **All Apps Update:**
1. **Checks all repositories** for changes
2. **Updates only those that changed**
3. **Logs all operations**
4. **Handles errors gracefully**

## 🔍 **Checking What Needs Updates:**

```bash
# Check current commit vs remote (for one app)
cd apps/n2s-tmmi-tracker
git log --oneline -1                    # Local commit
git ls-remote origin main               # Remote commit

# Use the monitor to check all repos
python3 scripts/polling/github-monitor.py --once
```

## ⚡ **Quick Reference:**

| Command | What it does |
|---------|--------------|
| `./scripts/manage-server.sh update n2s-tmmi-tracker` | Update TMMI tracker |
| `./scripts/manage-server.sh update n2s-impact-model` | Update impact model |
| `./scripts/manage-server.sh update all` | Update all apps |
| `./update-app n2s-tmmi-tracker` | Quick update shortcut |

## 🕐 **Automatic vs Manual:**

- **Automatic**: Runs every 5 minutes via systemd service
- **Manual**: Run anytime with above commands
- **Both use same logic**: Safe to mix automatic + manual

## 📊 **Monitoring:**

```bash
# Check automatic monitor status
sudo systemctl status github-repo-monitor

# View recent activity
tail -f logs/github-monitor.log

# View container logs after update
docker-compose logs n2s-tmmi-tracker
```

---

💡 **Tip**: Use `./scripts/manage-server.sh update all` for the easiest way to manually sync everything!
