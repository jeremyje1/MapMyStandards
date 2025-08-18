# A³E EC2 Deployment Guide

🚀 **Deploy your A³E system to EC2 with production-ready configuration**

## Prerequisites

### 1. EC2 Instance Setup
- ✅ **Instance**: `i-0d8227bf9f9e1a1ab` at `3.22.112.51`
- ✅ **AMI**: Ubuntu 22.04 LTS or newer
- ✅ **Instance Type**: t3.large or larger (minimum 2 vCPU, 8GB RAM)
- ✅ **Storage**: 50GB+ EBS volume
- ✅ **Security Group**: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (API)

### 2. Local Requirements
- SSH key pair for EC2 access
- AWS CLI configured (optional)
- Git repository access

### 3. DNS (Optional)
- Point your domain to `3.22.112.51`
- SSL certificate for HTTPS (Let's Encrypt recommended)

## Quick Deployment

### 1. One-Command Deploy
```bash
make deploy-ec2
```

This script will:
- ✅ Test SSH connection
- ✅ Install system dependencies (Docker, Git, etc.)
- ✅ Copy application files
- ✅ Build and start all services
- ✅ Verify deployment health

### 2. Verify Deployment
```bash
# Check status
make manage-ec2 COMMAND=status

# View logs
make manage-ec2 COMMAND=logs

# Test health
make manage-ec2 COMMAND=health
```

### 3. Access Your Application
- **API**: http://3.22.112.51:8000
- **Documentation**: http://3.22.112.51:8000/docs
- **Health Check**: http://3.22.112.51:8000/health

## Production Services

Your EC2 deployment includes:

### Core Application
- **A³E API**: FastAPI application with all endpoints
- **Nginx**: Reverse proxy with rate limiting and security headers
- **PostgreSQL**: Primary database with persistent storage
- **Redis**: Caching and session storage

### AI & Search
- **Milvus**: Vector database for semantic search
- **ETcd**: Milvus metadata storage
- **MinIO**: Object storage for Milvus

### Security & Monitoring
- Rate limiting (10 req/s API, 2 req/s uploads)
- Security headers (XSS, CSRF protection)
- Health checks for all services
- Centralized logging

## Management Commands

```bash
# Service Management
make manage-ec2 COMMAND=status      # Check all services
make manage-ec2 COMMAND=restart     # Restart all services
make manage-ec2 COMMAND=stop        # Stop all services
make manage-ec2 COMMAND=start       # Start all services

# Monitoring
make manage-ec2 COMMAND=logs        # View recent logs
make manage-ec2 COMMAND=monitor     # Live log monitoring
make manage-ec2 COMMAND=health      # Health check

# Maintenance
make manage-ec2 COMMAND=update      # Update application code
make manage-ec2 COMMAND=backup      # Create database backup
make manage-ec2 COMMAND=shell       # SSH into instance
```

## Configuration

### Environment Variables
Your production `.env` includes:
- Database connection to local PostgreSQL
- Milvus connection for vector search
- Redis for caching
- AWS Bedrock for LLM operations
- Production security settings

### Docker Compose
- **File**: `docker-compose.prod.yml`
- **Network**: Isolated Docker network
- **Volumes**: Persistent data storage
- **Health Checks**: Automatic service monitoring

### Nginx Configuration
- **Rate Limiting**: API protection
- **SSL Ready**: HTTPS configuration prepared
- **File Uploads**: 100MB max file size
- **Security Headers**: XSS, clickjacking protection

## Scaling & Performance

### Current Configuration
- **CPU**: 2+ cores for parallel processing
- **Memory**: 8GB+ for AI operations
- **Storage**: 50GB+ with auto-expansion
- **Network**: High-bandwidth for file uploads

### Optimization Tips
1. **Database**: Use RDS for production databases
2. **File Storage**: Use S3 for evidence documents
3. **Load Balancer**: Use ALB for multiple instances
4. **CDN**: CloudFront for static assets
5. **Monitoring**: CloudWatch for metrics

## Security Checklist

### ✅ Implemented
- SSH key-based authentication
- Docker network isolation
- Rate limiting and DDoS protection
- Security headers and XSS protection
- Database password protection
- LLM calls via AWS Bedrock (no data retention)

### 📝 Additional Recommendations
- SSL/TLS certificates for HTTPS
- VPC with private subnets
- AWS WAF for web application firewall
- Regular security updates
- Database encryption at rest
- Backup encryption

## Troubleshooting

### Service Issues
```bash
# Check service status
make manage-ec2 COMMAND=status

# View specific service logs
ssh ubuntu@3.22.112.51 'cd /home/ubuntu/a3e && sudo docker-compose logs postgres'
ssh ubuntu@3.22.112.51 'cd /home/ubuntu/a3e && sudo docker-compose logs a3e-app'
```

### Common Problems

#### Service Won't Start
```bash
# Check Docker daemon
ssh ubuntu@3.22.112.51 'sudo systemctl status docker'

# Check disk space
ssh ubuntu@3.22.112.51 'df -h'

# Check memory usage
ssh ubuntu@3.22.112.51 'free -h'
```

#### Database Connection Issues
```bash
# Test database connectivity
ssh ubuntu@3.22.112.51 'cd /home/ubuntu/a3e && sudo docker-compose exec postgres psql -U a3e -d a3e -c "SELECT 1;"'
```

#### API Not Responding
```bash
# Check application logs
make manage-ec2 COMMAND=logs

# Test internal connectivity
ssh ubuntu@3.22.112.51 'curl http://localhost:8000/health'
```

### Log Locations
- **Application**: `sudo docker-compose logs a3e-app`
- **Nginx**: `sudo docker-compose logs nginx`
- **Database**: `sudo docker-compose logs postgres`
- **Milvus**: `sudo docker-compose logs milvus`

## Backup & Recovery

### Automated Backups
```bash
# Create backup
make manage-ec2 COMMAND=backup

# Backups stored in: ./backups/a3e_backup_YYYYMMDD_HHMMSS.sql
```

### Manual Backup
```bash
# SSH to instance
make manage-ec2 COMMAND=shell

# Create backup
cd /home/ubuntu/a3e
sudo docker-compose exec postgres pg_dump -U a3e a3e > backup.sql
```

### Restore from Backup
```bash
# Copy backup to instance
scp -i ~/.ssh/id_rsa backup.sql ubuntu@3.22.112.51:/home/ubuntu/a3e/

# SSH and restore
ssh ubuntu@3.22.112.51
cd /home/ubuntu/a3e
sudo docker-compose exec -T postgres psql -U a3e -d a3e < backup.sql
```

## Monitoring & Alerts

### Health Monitoring
- **Endpoint**: http://3.22.112.51:8000/health
- **Check**: All services status
- **Response**: JSON with service health

### CloudWatch Integration (Optional)
```bash
# Install CloudWatch agent
sudo apt-get install amazon-cloudwatch-agent

# Configure monitoring
# - CPU utilization
# - Memory usage
# - Disk usage
# - Network traffic
```

## Next Steps

1. **SSL Certificate**: Set up HTTPS with Let's Encrypt
2. **Domain Setup**: Point your domain to the EC2 instance
3. **Monitoring**: Set up CloudWatch or external monitoring
4. **Backups**: Schedule regular automated backups
5. **Updates**: Plan for regular application updates

---

🎉 **Your A³E system is now running in production on EC2!**

**Access URLs:**
- **API**: http://3.22.112.51:8000
- **Docs**: http://3.22.112.51:8000/docs
- **Health**: http://3.22.112.51:8000/health
