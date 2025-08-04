# Secure Streamlit Server Architecture

## 🔒 Security-First Design

This is a **much more secure** alternative to the GitHub Actions push-based deployment.

### 🚫 **Problems with Previous Approach:**
- **Security risk**: SSH keys stored in GitHub secrets
- **Poor separation**: Apps needed to know server details  
- **No sandboxing**: Apps had full filesystem access
- **Resource abuse**: No limits on CPU/memory usage
- **Trust boundary**: Server trusted external GitHub Actions

### ✅ **New Secure Architecture:**

## 🏗️ **Server-Driven Polling System**

### **How It Works:**
1. **Server monitors** GitHub repositories every 5 minutes
2. **Detects changes** using GitHub API (no webhooks needed)
3. **Pulls updates** when new commits are found
4. **Restarts containers** with latest code
5. **Logs everything** for audit trail

### **Key Benefits:**
- **Zero external access** to server required
- **Apps don't know about server** - clean separation
- **Proper sandboxing** with Docker security features
- **Resource limits** prevent abuse
- **Rate limiting** via GitHub API
- **Full audit trail** in logs

## 🛡️ **Container Security Hardening**

### **Security Features Applied:**
```yaml
security_opt:
  - no-new-privileges:true    # Prevent privilege escalation
cap_drop: ['ALL']             # Drop all capabilities
cap_add: ['SETGID', 'SETUID'] # Add only minimum needed
read_only: true               # Read-only filesystem
user: nobody:nogroup          # Non-root user
tmpfs:                        # Writable temp directories only
  - /tmp:rw,noexec,nosuid,size=100m
```

### **Resource Limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'         # Max 1 CPU core
      memory: '512M'      # Max 512MB RAM
    reservations:
      cpus: '0.25'        # Guaranteed 0.25 CPU
      memory: '128M'      # Guaranteed 128MB RAM
```

### **Health Monitoring:**
```yaml
healthcheck:
  test: ['CMD', 'curl', '-f', 'http://localhost:8501/_stcore/health']
  interval: '30s'
  timeout: '10s'
  retries: 3
```

## 🎯 **Clean Architecture**

### **Separation of Concerns:**
- **Apps**: Focus only on business logic
- **Server**: Handles deployment and infrastructure
- **Monitor**: Watches for changes and triggers updates
- **Containers**: Provide isolated runtime environments

### **No Configuration Required in Apps:**
- Apps don't need GitHub Actions workflows
- Apps don't need server connection details
- Apps don't need deployment scripts
- Apps just need to work with Streamlit

## 📊 **Monitoring & Observability**

### **System Monitoring:**
```bash
# Monitor service status
sudo systemctl status github-repo-monitor

# View real-time logs
journalctl -u github-repo-monitor -f

# Check application logs
tail -f /mnt/storage/streamlit-server/logs/github-monitor.log
```

### **Container Health:**
```bash
# Check container status
docker-compose ps

# View app logs
docker-compose logs n2s-tmmi-tracker

# Monitor resources
docker stats
```

## 🔧 **Configuration**

### **Repository Configuration:**
Edit `/mnt/storage/streamlit-server/config/monitor-config.json`:

```json
{
  "repositories": [
    {
      "name": "n2s-tmmi-tracker",
      "owner": "miket-llc",
      "branch": "main",
      "path": "/mnt/storage/streamlit-server/apps/n2s-tmmi-tracker"
    }
  ],
  "poll_interval": 300,
  "max_retries": 3
}
```

### **Rate Limiting:**
- **GitHub API**: 60 requests/hour (unauthenticated)
- **With token**: 5000 requests/hour
- **Our usage**: ~24 requests/hour (2 repos × 12 polls/hour)

## 🚀 **Deployment Process**

### **For App Developers:**
1. **Develop** your Streamlit app
2. **Push to main branch** on GitHub
3. **Server detects** changes automatically
4. **App updates** within 5 minutes

### **Zero Configuration Required:**
- No GitHub Actions setup needed
- No secrets to manage
- No server connection details
- No deployment scripts

## 📈 **Scalability**

### **Adding New Apps:**
1. Add repository to config file
2. Clone app to apps directory  
3. Add to docker-compose
4. Restart monitor service

### **Multiple Servers:**
- Each server monitors independently
- No coordination required
- Can run identical configs
- Easy horizontal scaling

## 🔐 **Security Audit Trail**

### **All Actions Logged:**
- Repository check cycles
- Update detections
- Pull operations
- Container restarts
- Failures and errors

### **Log Locations:**
- **System logs**: `journalctl -u github-repo-monitor`
- **App logs**: `/mnt/storage/streamlit-server/logs/github-monitor.log`
- **Container logs**: `docker-compose logs <app-name>`

## 🎉 **Benefits Summary**

### **For Developers:**
- ✅ **Simple**: Just push code to GitHub
- ✅ **Fast**: Updates within 5 minutes
- ✅ **Clean**: No deployment complexity
- ✅ **Reliable**: Robust error handling

### **For Operations:**
- ✅ **Secure**: No external access required
- ✅ **Auditable**: Full logging and monitoring
- ✅ **Scalable**: Easy to add apps and servers
- ✅ **Maintainable**: Clear separation of concerns

### **For Security:**
- ✅ **Sandboxed**: Apps run in isolated containers
- ✅ **Limited**: Resource and capability restrictions
- ✅ **Monitored**: Health checks and logging
- ✅ **Controlled**: Server-driven updates only

---

This architecture provides **enterprise-grade security** while maintaining **developer simplicity**.
