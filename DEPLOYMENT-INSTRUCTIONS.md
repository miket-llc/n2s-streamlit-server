# N2S Streamlit Server Deployment Instructions

This guide describes how to deploy the N2S Streamlit Server platform to a new server.

## 🚀 Quick Deployment

### Prerequisites

- Supported OS: Ubuntu 24.04 LTS (or compatible Linux)
- Installed: Docker, Docker Compose, Git
- Open Ports: 80 (HTTP) and optionally 443 (HTTPS)

### Installation Steps

**1. Clone the repository**

```bash
cd /desired/installation/directory
sudo git clone https://github.com/miket-llc/n2s-streamlit-server.git
cd n2s-streamlit-server
```

**2. Run the installation script**

```bash
./deployment/server-setup/install-server.sh /mnt/storage/streamlit-server
```

**3. Follow the script prompts**
- The script will configure and start the server
- It will also set up systemd for auto-starting the server

**4. Post-installation checks**

After the script runs:
- Verify the server is running
- Access the web interface via `http://your-server-ip/`
- Confirm applications load correctly

## 🔄 Updating the Server

To update the server with new configurations or code:

```bash
cd /mnt/storage/streamlit-server
git pull origin main
./scripts/manage-server.sh restart
```

## 🚧 Troubleshooting

If you encounter problems during deployment:
1. **Check prerequisites** - Ensure all required software is installed
2. **Check network configuration** - Ensure ports are open
3. **Verify access permissions** - Check user permissions for directories
4. **Review logs** - Use the management scripts to view detailed logs

## 🤝 Support and Contribution

If you need help, please open an issue on the GitHub repository.

To contribute:
1. Fork the repo
2. Create a feature branch
3. Submit a pull request with clear commit history

## 📄 License

This project is licensed under the MIT License.
