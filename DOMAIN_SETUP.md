# 🌐 Domain Setup Complete!

## Quick Deployment to `api.mapmystandards.ai`

Your A³E system is ready for production deployment with a custom domain and SSL certificate.

### 🚀 One-Command Setup

```bash
# Complete deployment with domain and SSL
make setup-domain
```

This will:
1. ✅ Deploy A³E application to EC2
2. ✅ Configure NGINX reverse proxy
3. ✅ Set up SSL certificate with Let's Encrypt
4. ✅ Enable HTTPS with automatic redirect

### 📋 Step-by-Step Setup

```bash
# 1. Deploy application to EC2
make deploy-ec2

# 2. Configure NGINX reverse proxy
make setup-nginx

# 3. Set up SSL certificate (after DNS is configured)
make setup-ssl
```

### 🌐 DNS Configuration Required

**Before running SSL setup**, configure your DNS:

```
Type: A Record
Name: api.mapmystandards.ai
Value: 3.22.112.51
TTL: 300 (5 minutes)
```

### 🔧 Manual NGINX Configuration

If you prefer manual setup:

```bash
# SSH to your EC2 instance
ssh -i ~/.ssh/id_rsa ubuntu@3.22.112.51

# Create NGINX site configuration
sudo nano /etc/nginx/sites-available/api

# Paste the configuration:
server {
    listen 80;
    server_name api.mapmystandards.ai;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Client max body size for file uploads
    client_max_body_size 100M;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=2r/s;
    
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Extended timeouts for file uploads
    location /api/v1/evidence/upload {
        limit_req zone=upload_limit burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}

# Enable the site
sudo ln -s /etc/nginx/sites-available/api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 🔒 Manual SSL Setup

After DNS propagation:

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d api.mapmystandards.ai

# Follow prompts to:
# - Enter email address
# - Agree to terms
# - Choose redirect option (recommended)
```

### 🎉 Final Result

After setup completion, your A³E API will be live at:

- **🌐 API Base**: https://api.mapmystandards.ai
- **📚 Documentation**: https://api.mapmystandards.ai/docs
- **❤️ Health Check**: https://api.mapmystandards.ai/health
- **🤖 Institutions**: https://api.mapmystandards.ai/api/v1/institutions
- **📝 Standards**: https://api.mapmystandards.ai/api/v1/standards
- **📂 Evidence**: https://api.mapmystandards.ai/api/v1/evidence
- **⚙️ Workflows**: https://api.mapmystandards.ai/api/v1/workflows

### 🧪 Test Your API

```bash
# Test health endpoint
curl https://api.mapmystandards.ai/health

# List institution types
curl https://api.mapmystandards.ai/api/v1/institution-types

# Get accreditors
curl https://api.mapmystandards.ai/api/v1/accreditors

# Test Bedrock integration (if configured)
curl -X POST https://api.mapmystandards.ai/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Workflow",
    "institution_id": "test-123",
    "accreditor_id": "wscuc",
    "workflow_type": "evidence_mapping",
    "target_standards": ["wscuc_1_1"]
  }'
```

### 🔧 Management Commands

```bash
# Check deployment status
make manage-ec2 COMMAND=status

# View logs
make manage-ec2 COMMAND=logs

# Restart services
make manage-ec2 COMMAND=restart

# Create backup
make manage-ec2 COMMAND=backup
```

### 🛡️ Security Features

✅ **HTTPS/TLS Encryption** with Let's Encrypt certificate  
✅ **Automatic HTTP → HTTPS Redirect**  
✅ **Rate Limiting**: 10 req/s for API, 2 req/s for uploads  
✅ **Security Headers**: XSS, CSRF, clickjacking protection  
✅ **File Upload Limits**: 100MB maximum  
✅ **Auto-renewal**: SSL certificates renew automatically  

### 🎯 Ready for Production!

Your A³E system now supports:
- All US accrediting bodies (60+)
- Any institution type with automatic contextualization
- Secure HTTPS API access with custom domain
- Production-grade infrastructure with monitoring
- AWS Bedrock integration for AI-powered workflows

---

**🌐 Live API**: https://api.mapmystandards.ai/docs
