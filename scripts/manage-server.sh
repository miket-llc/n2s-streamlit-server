#!/bin/bash

# Streamlit server management script
# Usage: ./manage-server.sh [start|stop|restart|status|logs]

BASE_DIR="/mnt/storage/streamlit-server"
cd "$BASE_DIR"

case "$1" in
    start)
        echo "Starting Streamlit server..."
        docker-compose up -d
        echo "✅ Server started!"
        echo "🌐 Access at: http://your-server-ip/"
        ;;
    stop)
        echo "Stopping Streamlit server..."
        docker-compose down
        echo "✅ Server stopped!"
        ;;
    restart)
        echo "Restarting Streamlit server..."
        docker-compose restart
        echo "✅ Server restarted!"
        ;;
    status)
        echo "Server status:"
        docker-compose ps
        ;;
    logs)
        APP_NAME="$2"
        if [ -n "$APP_NAME" ]; then
            echo "Logs for $APP_NAME:"
            docker-compose logs -f "$APP_NAME"
        else
            echo "All logs:"
            docker-compose logs -f
        fi
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|status|logs [app-name]]"
        echo ""
        echo "Examples:"
        echo "  $0 start          # Start the server"
        echo "  $0 status         # Show running containers"
        echo "  $0 logs nginx     # Show nginx logs"
        echo "  $0 logs sample-app # Show sample app logs"
        exit 1
        ;;
esac
