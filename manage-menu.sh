#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Header function
show_header() {
    clear
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                 🚀 Streamlit Server Manager 🚀                ${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo
}

# Function to get available apps
get_available_apps() {
    if [ -f "config/monitor-config.json" ]; then
        python3 -c "import json; config=json.load(open('config/monitor-config.json')); print(' '.join(repo['name'] for repo in config['repositories']))"
    else
        echo "n2s-tmmi-tracker n2s-impact-model"
    fi
}

# Function to display menu options
display_menu() {
    echo -e "${GREEN}📋 Server Management Options:${NC}"
    echo
    echo "  1️⃣  Update Specific App"
    echo "  2️⃣  Update All Apps"
    echo "  3️⃣  Check GitHub Monitor Status"
    echo "  4️⃣  View Recent Monitor Logs"
    echo "  5️⃣  View Container Logs"
    echo "  6️⃣  Check Container Status"
    echo "  7️⃣  Manual Monitor Run (Once)"
    echo "  8️⃣  Show Available Apps"
    echo "  9️⃣  Exit"
    echo
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

# Function to show available apps (simple list)
show_apps() {
    echo -e "${YELLOW}📦 Available Apps:${NC}"
    available_apps=$(get_available_apps)
    for app in $available_apps; do
        echo "  • $app"
    done
    echo
}

# Function to update specific app
update_specific_app() {
    echo -e "${YELLOW}📦 Select App to Update:${NC}"
    available_apps=$(get_available_apps)
    app_array=($available_apps)
    local app_count=${#app_array[@]}
    
    # Show numbered list
    local i=1
    for app in $available_apps; do
        echo "  $i) $app"
        ((i++))
    done
    echo
    
    read -p "Select app number (1-$app_count): " app_choice
    
    if [[ "$app_choice" =~ ^[0-9]+$ ]] && [ "$app_choice" -ge 1 ] && [ "$app_choice" -le "$app_count" ]; then
        local selected_app="${app_array[$((app_choice-1))]}"
        echo -e "${YELLOW}🔄 Updating $selected_app...${NC}"
        ./scripts/manage-server.sh update "$selected_app"
    else
        echo -e "${RED}❌ Invalid selection${NC}"
    fi
    
    echo
    read -p "Press Enter to continue..."
}

# Function to update all apps
update_all_apps() {
    echo -e "${YELLOW}🔄 Updating all apps...${NC}"
    ./scripts/manage-server.sh update all
    
    echo
    read -p "Press Enter to continue..."
}

# Function to check monitor status
check_monitor_status() {
    echo -e "${YELLOW}📊 GitHub Monitor Service Status:${NC}"
    sudo systemctl status github-repo-monitor --no-pager
    
    echo
    read -p "Press Enter to continue..."
}

# Function to view recent logs
view_recent_logs() {
    echo -e "${YELLOW}📋 Recent Monitor Logs (Press Ctrl+C to exit):${NC}"
    echo
    if [ -f "logs/github-monitor.log" ]; then
        tail -f logs/github-monitor.log
    else
        echo -e "${RED}❌ Log file not found: logs/github-monitor.log${NC}"
    fi
    
    echo
    read -p "Press Enter to continue..."
}

# Function to view container logs with selection
view_container_logs() {
    echo -e "${YELLOW}📋 Select Container for Logs:${NC}"
    echo "  0) All containers"
    
    available_apps=$(get_available_apps)
    local i=1
    for app in $available_apps; do
        echo "  $i) $app"
        ((i++))
    done
    echo
    
    app_array=($available_apps)
    local app_count=${#app_array[@]}
    
    read -p "Select option (0-$app_count): " log_choice
    
    local container_name=""
    if [ "$log_choice" = "0" ]; then
        container_name="all"
    elif [[ "$log_choice" =~ ^[0-9]+$ ]] && [ "$log_choice" -ge 1 ] && [ "$log_choice" -le "$app_count" ]; then
        container_name="${app_array[$((log_choice-1))]}"
    else
        echo -e "${RED}❌ Invalid selection${NC}"
        return
    fi
    
    echo -e "${YELLOW}📋 Container Logs for $container_name (Press Ctrl+C to exit):${NC}"
    echo
    
    if [ "$container_name" = "all" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$container_name"
    fi
    
    echo
    read -p "Press Enter to continue..."
}

# Function to check container status
check_container_status() {
    echo -e "${YELLOW}📊 Container Status:${NC}"
    docker-compose ps
    
    echo
    read -p "Press Enter to continue..."
}

# Function to run manual monitor
manual_monitor_run() {
    echo -e "${YELLOW}🔄 Running manual monitor check...${NC}"
    python3 scripts/polling/github-monitor.py --once
    
    echo
    read -p "Press Enter to continue..."
}

# Main menu loop
while true; do
    show_header
    display_menu
    
    read -p "Select an option (1-9): " choice
    echo
    
    case $choice in
        1)
            update_specific_app
            ;;
        2)
            update_all_apps
            ;;
        3)
            check_monitor_status
            ;;
        4)
            view_recent_logs
            ;;
        5)
            view_container_logs
            ;;
        6)
            check_container_status
            ;;
        7)
            manual_monitor_run
            ;;
        8)
            show_apps
            read -p "Press Enter to continue..."
            ;;
        9)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            break
            ;;
        *)
            echo -e "${RED}❌ Invalid option selected. Please try again.${NC}"
            sleep 2
            ;;
    esac
done
