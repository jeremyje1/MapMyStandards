# AWS S3 Setup for MapMyStandards

## Quick Setup Guide (10 minutes)

### Step 1: Create S3 Bucket

1. Go to [AWS S3 Console](https://console.aws.amazon.com/s3/)
2. Click "Create bucket"
3. **Bucket name**: `mapmystandards-uploads` (or your preferred name)
4. **Region**: `us-east-1` (or your preferred region)
5. **Block Public Access**: Keep all settings CHECKED (we'll use presigned URLs)
6. Click "Create bucket"

### Step 2: Set CORS Policy

1. Go to your bucket → **Permissions** tab
2. Scroll to **Cross-origin resource sharing (CORS)**
3. Click **Edit** and paste:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
        "AllowedOrigins": [
            "https://mapmystandards.ai",
            "https://*.mapmystandards.ai",
            "http://localhost:3000"
        ],
        "ExposeHeaders": ["ETag", "x-amz-server-side-encryption"],
        "MaxAgeSeconds": 3600
    }
]
```

### Step 3: Create IAM User for API Access

1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Click **Users** → **Add users**
3. **User name**: `mapmystandards-api`
4. Check **Access key - Programmatic access**
5. Click **Next: Permissions**
6. Click **Attach existing policies directly**
7. Click **Create policy** and use this JSON:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:GetObjectAcl",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::mapmystandards-uploads",
                "arn:aws:s3:::mapmystandards-uploads/*"
            ]
        }
    ]
}
```

8. Name the policy: `MapMyStandardsS3Access`
9. Go back and attach this policy to your user
10. Complete user creation
11. **SAVE THE ACCESS KEY AND SECRET KEY**

### Step 4: Set Railway Environment Variables

```bash
railway variables --set "AWS_ACCESS_KEY_ID=AKIA..." \
  --set "AWS_SECRET_ACCESS_KEY=..." \
  --set "AWS_REGION=us-east-1" \
  --set "S3_BUCKET=mapmystandards-uploads" \
  --set "STORAGE_PROVIDER=aws"
```

### Step 5: (Optional) CloudFront CDN Setup

For faster global delivery:

1. Go to [CloudFront Console](https://console.aws.amazon.com/cloudfront/)
2. Click **Create Distribution**
3. **Origin Domain**: Select your S3 bucket
4. **Origin Access**: Choose **Origin access control**
5. **Viewer Protocol Policy**: **Redirect HTTP to HTTPS**
6. **Allowed HTTP Methods**: **GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE**
7. **Cache Policy**: Choose **CachingOptimized**
8. Create distribution
9. Copy the distribution domain (like `d1234567.cloudfront.net`)
10. Add to Railway:

```bash
railway variables --set "CLOUDFRONT_URL=https://d1234567.cloudfront.net"
```

## Test Your Setup

```python
# Quick test script
import boto3

s3 = boto3.client(
    's3',
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY',
    region_name='us-east-1'
)

# Test listing bucket
response = s3.list_objects_v2(Bucket='mapmystandards-uploads')
print("✅ S3 connection successful!" if response else "❌ Failed")
```

## Estimated Costs

- **Storage**: $0.023/GB/month
- **Requests**: $0.0004 per 1,000 requests  
- **Data Transfer**: First 100GB/month free to internet
- **Typical monthly cost**: <$5 for most startups

## Security Best Practices

1. ✅ Never commit AWS keys to git
2. ✅ Use IAM roles with minimal permissions
3. ✅ Enable S3 versioning for recovery
4. ✅ Set up lifecycle policies to delete old files
5. ✅ Enable CloudTrail for audit logs

Ready to proceed with AWS S3?