#!/usr/bin/env bash
"""
A3E EC2 Management Script

Provides common management commands for the deployed A3E application.
"""

set -e

# Load environment variables
source .env

# Configuration
EC2_USER="ubuntu"
SSH_KEY_PATH="~/.ssh/id_rsa"
REMOTE_APP_DIR="/home/$EC2_USER/a3e"

# Function to run commands on EC2
run_remote() {
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$1"
}

# Function to display usage
usage() {
    echo "A3E EC2 Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  status      - Show service status"
    echo "  logs        - Show application logs"
    echo "  restart     - Restart all services"
    echo "  stop        - Stop all services"
    echo "  start       - Start all services"
    echo "  shell       - SSH into the EC2 instance"
    echo "  update      - Update application code"
    echo "  backup      - Backup database"
    echo "  health      - Check application health"
    echo "  monitor     - Monitor logs in real-time"
    echo ""
    echo "Environment:"
    echo "  EC2_HOST: $EC2_HOST"
    echo "  INSTANCE: $EC2_INSTANCE_ID"
}

case "${1:-}" in
    status)
        echo "📊 Checking service status..."
        run_remote "cd $REMOTE_APP_DIR && sudo docker-compose ps"
        ;;
    
    logs)
        echo "📝 Application logs (last 100 lines):"
        run_remote "cd $REMOTE_APP_DIR && sudo docker-compose logs --tail=100"
        ;;
    
    restart)
        echo "🔄 Restarting services..."
        run_remote "cd $REMOTE_APP_DIR && sudo docker-compose restart"
        echo "✅ Services restarted"
        ;;
    
    stop)
        echo "🛑 Stopping services..."
        run_remote "cd $REMOTE_APP_DIR && sudo docker-compose down"
        echo "✅ Services stopped"
        ;;
    
    start)
        echo "🚀 Starting services..."
        run_remote "cd $REMOTE_APP_DIR && sudo docker-compose up -d"
        echo "✅ Services started"
        ;;
    
    shell)
        echo "🐚 Connecting to EC2 instance..."
        ssh -i "$SSH_KEY_PATH" "$EC2_USER@$EC2_HOST"
        ;;
    
    update)
        echo "🔄 Updating application..."
        echo "📤 Copying new files..."
        scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -r . "$EC2_USER@$EC2_HOST:$REMOTE_APP_DIR/"
        echo "🏗️ Rebuilding and restarting..."
        run_remote "cd $REMOTE_APP_DIR && sudo docker-compose build && sudo docker-compose up -d"
        echo "✅ Application updated"
        ;;
    
    backup)
        echo "💾 Creating database backup..."
        BACKUP_FILE="a3e_backup_$(date +%Y%m%d_%H%M%S).sql"
        run_remote "cd $REMOTE_APP_DIR && sudo docker-compose exec -T postgres pg_dump -U a3e a3e > $BACKUP_FILE"
        echo "📥 Downloading backup..."
        scp -i "$SSH_KEY_PATH" "$EC2_USER@$EC2_HOST:$REMOTE_APP_DIR/$BACKUP_FILE" "./backups/"
        echo "✅ Backup saved to ./backups/$BACKUP_FILE"
        ;;
    
    health)
        echo "🔍 Checking application health..."
        if run_remote "curl -f http://localhost:8000/health"; then
            echo "✅ Application is healthy"
            echo "🌐 External access: http://$EC2_HOST:8000"
        else
            echo "❌ Application health check failed"
            echo "📝 Recent logs:"
            run_remote "cd $REMOTE_APP_DIR && sudo docker-compose logs --tail=20"
        fi
        ;;
    
    monitor)
        echo "📊 Monitoring logs (Ctrl+C to exit)..."
        run_remote "cd $REMOTE_APP_DIR && sudo docker-compose logs -f"
        ;;
    
    *)
        usage
        exit 1
        ;;
esac
