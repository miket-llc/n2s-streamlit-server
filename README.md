# N2S Streamlit Server

A professional, containerized Streamlit hosting platform with automated CI/CD deployment capabilities.

## 🚀 Features

- **Docker-based** containerization for app isolation
- **Nginx reverse proxy** for routing and load balancing  
- **Automated CI/CD** deployment via GitHub Actions
- **Zero-downtime deployments** with health checks
- **SSL/TLS support** ready
- **Centralized logging** and monitoring
- **Template-based** app scaffolding
- **Secrets management** with Streamlit secrets.toml

## 📁 Architecture

```
/mnt/storage/streamlit-server/
├── README.md                           # This file
├── DEPLOYMENT-SETUP.md                 # CI/CD setup guide
├── docker-compose.yml                  # Container orchestration
├── apps/                               # Deployed Streamlit applications
├── nginx/                              # Nginx configuration
│   ├── nginx.conf                      # Main nginx config
│   └── conf.d/streamlit.conf          # App routing rules
├── scripts/                            # Management and deployment scripts
│   ├── manage-server.sh               # Start/stop/status server
│   ├── deploy-methods/                # Deployment scripts
│   ├── webhook/                       # GitHub Actions integration
│   └── templates/                     # App and config templates
├── github-actions-templates/          # CI/CD workflow templates
├── logs/                              # Application and deployment logs
└── ssl/                               # SSL certificates (optional)
```

## 🛠️ Quick Start

### Prerequisites

- Ubuntu 24.04 LTS (or compatible Linux)
- Docker and Docker Compose
- Git
- Port 80 and 443 forwarded to this server

### Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/miket-llc/n2s-streamlit-server.git
   cd n2s-streamlit-server
   ```

2. **Start the server:**
   ```bash
   ./scripts/manage-server.sh start
   ```

3. **Access the dashboard:**
   - Open `http://your-server-ip/` in your browser

## 📱 App Management

### Deploy from GitHub Repository

```bash
./scripts/deploy-methods/git-deploy.sh <repo_url> [app_name] [branch]
```

**Example:**
```bash
./scripts/deploy-methods/git-deploy.sh https://github.com/user/my-app.git my-app main
```

### Create New App Template

```bash
./scripts/create-app-template.sh <app-name>
```

### Server Management

```bash
# Start all services
./scripts/manage-server.sh start

# Stop all services  
./scripts/manage-server.sh stop

# Restart services
./scripts/manage-server.sh restart

# View status
./scripts/manage-server.sh status

# View logs
./scripts/manage-server.sh logs [app-name]
```

## 🔄 CI/CD with GitHub Actions

Set up automated deployment for your Streamlit repositories:

1. **Follow the setup guide:** [DEPLOYMENT-SETUP.md](DEPLOYMENT-SETUP.md)
2. **Add workflow files** from `github-actions-templates/` to your repos
3. **Configure GitHub Secrets** for server access
4. **Push to main branch** → automatic deployment! 🚀

### Supported Repositories

Currently configured for:
- [miket-llc/n2s-tmmi-tracker](https://github.com/miket-llc/n2s-tmmi-tracker)
- [miket-llc/n2s-impact-model](https://github.com/miket-llc/n2s-impact-model)

## 🏗️ App Requirements

For successful deployment, your Streamlit app should have:

- **Main file:** `app.py`, `streamlit_app.py`, or `main.py`
- **Dependencies:** `requirements.txt`
- **Secrets (optional):** `.streamlit/secrets.toml`

### Example App Structure

```
my-streamlit-app/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── secrets.toml         # App configuration (optional)
├── data/                    # Data files (optional)
├── modules/                 # Additional Python modules (optional)
└── README.md               # App documentation
```

## 🔐 Security Features

- **Container isolation** - Each app runs in its own container
- **Secrets management** - Sensitive data stored in secrets.toml
- **Rate limiting** - Built-in nginx rate limiting
- **SSH key authentication** - Secure GitHub Actions deployment
- **Non-root containers** - Security best practices

## 📊 Monitoring

### View Running Apps

```bash
docker-compose ps
```

### App-specific Logs

```bash
docker-compose logs -f <app-name>
```

### System Resource Usage

```bash
docker stats
```

### Deployment History

```bash
tail -f logs/deploy.log
```

## 🌐 Network Configuration

### Required Port Forwarding

Forward these ports from your router to this server:
- **Port 80** (HTTP)
- **Port 443** (HTTPS) - Optional, for SSL

### App URLs

Apps are automatically available at:
- `http://your-server-ip/<app-name>/`

## 🔧 Troubleshooting

### Common Issues

**App not loading:**
1. Check container status: `docker-compose ps`
2. View app logs: `docker-compose logs <app-name>`
3. Verify requirements.txt exists and is valid

**Deployment failed:**
1. Check deployment logs: `tail -f logs/deploy.log`
2. Verify GitHub secrets are configured correctly
3. Ensure server SSH access is working

**Nginx errors:**
1. Test nginx config: `docker-compose exec nginx nginx -t`
2. Rebuild config: `./scripts/rebuild-nginx-config.sh`
3. Restart nginx: `docker-compose restart nginx`

### Getting Help

1. Check the logs first: `./scripts/manage-server.sh logs`
2. Verify all containers are running: `./scripts/manage-server.sh status`
3. Review the deployment setup: [DEPLOYMENT-SETUP.md](DEPLOYMENT-SETUP.md)

## 🚀 Advanced Configuration

### SSL/TLS Setup

1. Place certificates in `ssl/` directory
2. Update nginx configuration in `nginx/conf.d/streamlit.conf`
3. Restart nginx: `docker-compose restart nginx`

### Custom Domain

1. Configure DNS to point to your server
2. Update nginx server_name directives
3. Set up SSL certificates (recommended: Let's Encrypt)

### Load Balancing

For high-traffic apps, you can configure multiple container instances:

1. Modify `docker-compose.yml` to add replicas
2. Update nginx upstream configuration
3. Deploy with: `docker-compose up -d --scale <app-name>=3`

## 📋 Maintenance

### Regular Tasks

- **Monitor disk space:** Apps and logs can grow over time
- **Update base images:** Regularly pull new Python base images
- **Review logs:** Check for errors or security issues
- **Backup configurations:** Keep copies of important configs

### Updates

To update the server configuration:

```bash
git pull origin main
./scripts/manage-server.sh restart
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with Docker and Nginx
- Streamlit framework by Snowflake
- GitHub Actions for CI/CD
- Ubuntu 24.04 LTS

---

**Made with ❤️ for professional Streamlit app hosting**
