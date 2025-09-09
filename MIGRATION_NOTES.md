# MapMyStandards Platform Migration Notes

## Overview
This document outlines the key changes and configuration requirements for the unified MapMyStandards platform implementation.

## Architecture Changes

### Authentication System
- **JWT-based auth** with httpOnly cookies for security
- Access tokens: 15-30 minute expiry
- Refresh tokens: 7 days default, 30 days with "Remember Me"
- Password hashing: Argon2id (replacing basic SHA256)
- Session management in database for revocation

### File Upload System
- **Direct-to-storage uploads** using presigned URLs
- Removed local disk storage (`/uploads/` directory)
- S3/R2/Supabase Storage compatible
- Client-side progress tracking
- Automatic file organization: `org/{orgId}/user/{userId}/{uuid}-{filename}`

### CORS Configuration
```
Allowed Origins:
- https://mapmystandards.ai
- https://www.mapmystandards.ai  
- https://api.mapmystandards.ai
- https://platform.mapmystandards.ai
```

## Environment Variables

### Required Variables

#### Authentication
```bash
JWT_SECRET_KEY=          # 32+ character secret for JWT signing
ENVIRONMENT=             # development | staging | production
```

#### Database
```bash
DATABASE_URL=            # PostgreSQL connection string
```

#### Storage (Choose one)
```bash
# AWS S3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=

# OR Supabase Storage
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_STORAGE_BUCKET=
```

#### Email Service
```bash
POSTMARK_API_KEY=        # Postmark API key
POSTMARK_FROM_EMAIL=     # Verified sender email
SUPPORT_EMAIL=           # Support inbox
```

#### Stripe
```bash
STRIPE_SECRET_KEY=       # Stripe secret key
STRIPE_WEBHOOK_SECRET=   # Webhook endpoint secret
STRIPE_PRICE_ID_ESSENTIAL=
STRIPE_PRICE_ID_PROFESSIONAL=
STRIPE_PRICE_ID_ENTERPRISE=
```

#### URLs
```bash
NEXT_PUBLIC_URL=https://mapmystandards.ai
NEXT_PUBLIC_API_URL=https://api.mapmystandards.ai
CLOUDFRONT_URL=          # Optional: CDN for file downloads
```

## Cookie Configuration

Set cookies with proper domain scope:
```
Domain: .mapmystandards.ai
Secure: true
HttpOnly: true
SameSite: Lax
Path: /
```

## Storage Bucket Policies

### S3 Bucket CORS
```json
{
  "CORSRules": [{
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": [
      "https://mapmystandards.ai",
      "https://platform.mapmystandards.ai"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }]
}
```

### S3 Bucket Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowPresignedUploads",
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::ACCOUNT:user/mapmystandards-api"
    },
    "Action": [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:GetObject",
      "s3:DeleteObject"
    ],
    "Resource": "arn:aws:s3:::BUCKET/org/*"
  }]
}
```

## Database Migrations

Run the following migrations in order:

1. **Auth tables enhancement**
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_expires TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS newsletter_opt_in BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
```

2. **Documents table**
```sql
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    organization_id VARCHAR(255),
    filename VARCHAR(255) NOT NULL,
    file_key VARCHAR(500) UNIQUE NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100),
    sha256 VARCHAR(64),
    status VARCHAR(50) DEFAULT 'uploaded',
    error_message TEXT,
    analysis_id VARCHAR(36),
    extracted_text TEXT,
    page_count INTEGER,
    word_count INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
```

3. **Analyses table**
```sql
CREATE TABLE IF NOT EXISTS analyses (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    document_id VARCHAR(36) REFERENCES documents(id),
    analysis_type VARCHAR(50) NOT NULL,
    standards_set VARCHAR(100),
    configuration TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    error_message TEXT,
    results TEXT,
    mapped_standards TEXT,
    confidence_score FLOAT,
    quick_wins TEXT,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_document_id ON analyses(document_id);
CREATE INDEX idx_analyses_status ON analyses(status);
```

## Testing

### Unit Tests
```bash
pytest tests/test_auth.py -v       # Auth endpoints
pytest tests/test_upload.py -v     # Upload endpoints
```

### E2E Tests (Playwright)
```bash
# Test remember-me functionality
npx playwright test tests/e2e/auth.spec.ts

# Test file upload
npx playwright test tests/e2e/upload.spec.ts
```

## Deployment Checklist

### Backend (FastAPI on Railway)
1. ✅ Set all environment variables
2. ✅ Run database migrations
3. ✅ Configure CORS middleware
4. ✅ Test auth endpoints
5. ✅ Verify S3 presigned URLs work
6. ✅ Check webhook endpoints

### Frontend (Next.js on Vercel)
1. ✅ Set NEXT_PUBLIC_* variables
2. ✅ Configure API routes
3. ✅ Test Stripe checkout flow
4. ✅ Verify upload component works
5. ✅ Check cookie domain scope

### Post-Deployment
1. ✅ Verify cookies work across subdomains
2. ✅ Test password reset email flow
3. ✅ Upload a test document
4. ✅ Run an analysis
5. ✅ Complete a Stripe checkout

## Security Notes

1. **Never commit secrets** - Use environment variables
2. **Validate file uploads** - Check MIME types and sizes
3. **Sanitize user input** - Prevent XSS and SQL injection
4. **Use HTTPS everywhere** - No mixed content
5. **Implement rate limiting** - Prevent abuse
6. **Log security events** - Track failed logins, etc.

## Monitoring

Key metrics to track:
- Authentication success/failure rates
- Upload completion rates
- Analysis processing times
- Stripe webhook failures
- API response times
- Error rates by endpoint

## Support

For issues or questions:
- Technical: engineering@mapmystandards.ai
- Platform: support@mapmystandards.ai
- Security: security@mapmystandards.ai