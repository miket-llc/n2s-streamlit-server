#!/bin/bash

# N2S Impact Model Management Script
# Common operations for managing the deployed application

set -e

SERVER="motoko.hopto.org"
PORT="2222"
REMOTE_USER="${USER}"
SERVICE_NAME="n2s-impact-model"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run commands on remote server
run_remote() {
    ssh -p ${PORT} ${REMOTE_USER}@${SERVER} "$1"
}

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show help
show_help() {
    echo "N2S Impact Model Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  status     - Check application status"
    echo "  logs       - View application logs (follow mode)"
    echo "  restart    - Restart the application"
    echo "  stop       - Stop the application"
    echo "  start      - Start the application"
    echo "  deploy     - Deploy/update the application"
    echo "  backup     - Create a backup of the application"
    echo "  restore    - Restore from backup"
    echo "  nginx      - Check Nginx status and configuration"
    echo "  ssl        - Check SSL certificate status"
    echo "  cleanup    - Remove old logs and temporary files"
    echo "  health     - Comprehensive health check"
    echo "  help       - Show this help message"
}

# Command implementations
cmd_status() {
    print_status "Checking application status..."
    run_remote "sudo systemctl status ${SERVICE_NAME} --no-pager -l"
}

cmd_logs() {
    print_status "Following application logs (Press Ctrl+C to exit)..."
    run_remote "sudo journalctl -f -u ${SERVICE_NAME}"
}

cmd_restart() {
    print_status "Restarting application..."
    run_remote "sudo systemctl restart ${SERVICE_NAME}"
    sleep 2
    cmd_status
    print_success "Application restarted"
}

cmd_stop() {
    print_status "Stopping application..."
    run_remote "sudo systemctl stop ${SERVICE_NAME}"
    print_success "Application stopped"
}

cmd_start() {
    print_status "Starting application..."
    run_remote "sudo systemctl start ${SERVICE_NAME}"
    sleep 2
    cmd_status
    print_success "Application started"
}

cmd_deploy() {
    print_status "Deploying application..."
    ./deploy.sh
}

cmd_backup() {
    BACKUP_NAME="n2s-backup-$(date +%Y%m%d-%H%M%S)"
    print_status "Creating backup: ${BACKUP_NAME}"
    
    run_remote "sudo systemctl stop ${SERVICE_NAME}"
    run_remote "cd /home/${REMOTE_USER} && tar -czf ${BACKUP_NAME}.tar.gz n2s-impact-model"
    run_remote "sudo systemctl start ${SERVICE_NAME}"
    
    print_success "Backup created: ${BACKUP_NAME}.tar.gz"
}

cmd_restore() {
    if [ -z "$2" ]; then
        print_error "Please specify backup file name"
        echo "Usage: $0 restore BACKUP_NAME.tar.gz"
        exit 1
    fi
    
    BACKUP_FILE="$2"
    print_warning "This will replace the current application with backup: ${BACKUP_FILE}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Restoring from backup..."
        run_remote "sudo systemctl stop ${SERVICE_NAME}"
        run_remote "cd /home/${REMOTE_USER} && rm -rf n2s-impact-model && tar -xzf ${BACKUP_FILE}"
        run_remote "sudo systemctl start ${SERVICE_NAME}"
        print_success "Restore completed"
    else
        print_status "Restore cancelled"
    fi
}

cmd_nginx() {
    print_status "Checking Nginx status..."
    run_remote "sudo systemctl status nginx --no-pager -l"
    echo ""
    print_status "Testing Nginx configuration..."
    run_remote "sudo nginx -t"
}

cmd_ssl() {
    print_status "Checking SSL certificate status..."
    run_remote "sudo certbot certificates" || print_warning "Certbot not installed or no certificates found"
}

cmd_cleanup() {
    print_status "Cleaning up old logs and temporary files..."
    run_remote "sudo journalctl --vacuum-time=7d"
    run_remote "cd /home/${REMOTE_USER} && find . -name '*.pyc' -delete"
    run_remote "cd /home/${REMOTE_USER} && find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"
    print_success "Cleanup completed"
}

cmd_health() {
    print_status "Running comprehensive health check..."
    
    echo "🔍 System Status:"
    run_remote "uptime"
    echo ""
    
    echo "🔍 Application Service:"
    if run_remote "sudo systemctl is-active ${SERVICE_NAME} >/dev/null 2>&1"; then
        print_success "Service is running"
    else
        print_error "Service is not running"
    fi
    echo ""
    
    echo "🔍 Nginx Status:"
    if run_remote "sudo systemctl is-active nginx >/dev/null 2>&1"; then
        print_success "Nginx is running"
    else
        print_error "Nginx is not running"
    fi
    echo ""
    
    echo "🔍 Port Checks:"
    if run_remote "ss -tln | grep :80 >/dev/null"; then
        print_success "Port 80 is listening"
    else
        print_warning "Port 80 is not listening"
    fi
    
    if run_remote "ss -tln | grep :8501 >/dev/null"; then
        print_success "Port 8501 (Streamlit) is listening"
    else
        print_warning "Port 8501 is not listening"
    fi
    echo ""
    
    echo "🔍 Disk Usage:"
    run_remote "df -h /home"
    echo ""
    
    echo "🔍 Memory Usage:"
    run_remote "free -h"
    echo ""
    
    print_status "Health check completed"
}

# Main script logic
case "${1:-help}" in
    status)     cmd_status ;;
    logs)       cmd_logs ;;
    restart)    cmd_restart ;;
    stop)       cmd_stop ;;
    start)      cmd_start ;;
    deploy)     cmd_deploy ;;
    backup)     cmd_backup "$@" ;;
    restore)    cmd_restore "$@" ;;
    nginx)      cmd_nginx ;;
    ssl)        cmd_ssl ;;
    cleanup)    cmd_cleanup ;;
    health)     cmd_health ;;
    help|*)     show_help ;;
esac 