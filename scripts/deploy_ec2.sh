#!/usr/bin/env bash
"""
A3E EC2 Deployment Script

Deploys the A3E application to the specified EC2 instance.
"""

set -e

# Load environment variables
source .env

# Configuration
EC2_USER="ubuntu"  # Default for Ubuntu AMI, change if different
SSH_KEY_PATH="~/.ssh/id_rsa"  # Update with your SSH key path
REMOTE_APP_DIR="/home/$EC2_USER/a3e"
DOCKER_COMPOSE_VERSION="2.20.0"

echo "🚀 Starting A3E deployment to EC2..."
echo "📍 Target: $EC2_HOST ($EC2_INSTANCE_ID)"

# Function to run commands on EC2
run_remote() {
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$1"
}

# Function to copy files to EC2
copy_to_remote() {
    scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -r "$1" "$EC2_USER@$EC2_HOST:$2"
}

echo "🔗 Testing SSH connection..."
if run_remote "echo 'SSH connection successful'"; then
    echo "✅ SSH connection established"
else
    echo "❌ SSH connection failed. Please check:"
    echo "   - SSH key path: $SSH_KEY_PATH"
    echo "   - EC2 instance is running"
    echo "   - Security group allows SSH (port 22)"
    echo "   - Correct username: $EC2_USER"
    exit 1
fi

echo "📦 Installing system dependencies..."
run_remote "sudo apt-get update"
run_remote "sudo apt-get install -y git curl docker.io docker-compose python3-pip"

echo "🐳 Setting up Docker..."
run_remote "sudo systemctl start docker"
run_remote "sudo systemctl enable docker"
run_remote "sudo usermod -aG docker $EC2_USER"

echo "📁 Preparing application directory..."
run_remote "mkdir -p $REMOTE_APP_DIR"
run_remote "cd $REMOTE_APP_DIR && rm -rf *"

echo "📤 Copying application files..."
copy_to_remote "." "$REMOTE_APP_DIR/"

echo "🔧 Setting up environment..."
# Update .env for production
run_remote "cd $REMOTE_APP_DIR && sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' .env"
run_remote "cd $REMOTE_APP_DIR && sed -i 's/DEBUG=true/DEBUG=false/' .env"
run_remote "cd $REMOTE_APP_DIR && sed -i 's/localhost/localhost/' .env"  # Keep localhost for local Docker network

echo "🏗️ Building application..."
run_remote "cd $REMOTE_APP_DIR && sudo docker-compose build"

echo "🚀 Starting services..."
run_remote "cd $REMOTE_APP_DIR && sudo docker-compose up -d"

echo "⏳ Waiting for services to start..."
sleep 30

echo "🧪 Testing deployment..."
if run_remote "curl -f http://localhost:8000/health"; then
    echo "✅ Application is running successfully!"
    echo "🌐 Access your application at: http://$EC2_HOST:8000"
    echo "📚 API documentation: http://$EC2_HOST:8000/docs"
else
    echo "❌ Application health check failed"
    echo "📝 Checking logs..."
    run_remote "cd $REMOTE_APP_DIR && sudo docker-compose logs --tail=50"
    exit 1
fi

echo "🔍 Service status:"
run_remote "cd $REMOTE_APP_DIR && sudo docker-compose ps"

echo ""
echo "🎉 Deployment complete!"
echo "📊 Dashboard: http://$EC2_HOST:8000"
echo "📖 API Docs: http://$EC2_HOST:8000/docs"
echo "🔍 Health: http://$EC2_HOST:8000/health"
echo ""
echo "Useful commands:"
echo "  SSH to instance: ssh -i $SSH_KEY_PATH $EC2_USER@$EC2_HOST"
echo "  View logs: ssh -i $SSH_KEY_PATH $EC2_USER@$EC2_HOST 'cd $REMOTE_APP_DIR && sudo docker-compose logs -f'"
echo "  Restart: ssh -i $SSH_KEY_PATH $EC2_USER@$EC2_HOST 'cd $REMOTE_APP_DIR && sudo docker-compose restart'"
echo "  Stop: ssh -i $SSH_KEY_PATH $EC2_USER@$EC2_HOST 'cd $REMOTE_APP_DIR && sudo docker-compose down'"
