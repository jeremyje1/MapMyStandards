# AWS S3 Upload Configuration Guide

## Issue Fixed
Documents were showing 0 bytes because they were being saved to local storage on Railway, which doesn't persist files. The fix implements proper cloud storage using AWS S3.

## Required Environment Variables on Railway

Add these environment variables to your Railway deployment:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1  # or your preferred region

# S3 Bucket Name
S3_BUCKET_NAME=mapmystandards-uploads  # or your bucket name
```

## AWS S3 Setup Steps

1. **Create S3 Bucket** (if not already created):
   ```bash
   aws s3 mb s3://mapmystandards-uploads --region us-east-1
   ```

2. **Create IAM User** with S3 access:
   - Go to AWS IAM Console
   - Create new user (e.g., `mapmystandards-api`)
   - Attach policy: `AmazonS3FullAccess` or create custom policy:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
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

3. **Configure CORS** on S3 bucket (for direct browser uploads):
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
       "AllowedOrigins": [
         "https://platform.mapmystandards.ai",
         "https://*.mapmystandards.ai"
       ],
       "ExposeHeaders": ["ETag"],
       "MaxAgeSeconds": 3000
     }
   ]
   ```

## What Was Changed

1. **Updated `/api/user/intelligence-simple/evidence/upload` endpoint**:
   - Now uses `StorageService` instead of local file storage
   - Checks for empty files (0 bytes) and skips them
   - Generates unique storage keys for each file
   - Saves metadata with each upload
   - Returns storage type in response

2. **Storage Service Features**:
   - Automatically uses S3 if credentials are configured
   - Falls back to local storage if S3 is not available
   - Calculates SHA256 hash for each file
   - Supports presigned URLs for direct downloads

## Verification

After setting up AWS credentials on Railway:

1. Upload a document through the platform
2. Check the response - it should show:
   ```json
   {
     "storage_type": "s3",
     "size": [actual file size],
     "status": "uploaded"
   }
   ```
3. Documents should persist and be retrievable
4. Dashboard should show correct document count

## Troubleshooting

- If still seeing 0 bytes, check Railway logs for S3 connection errors
- Ensure AWS credentials have proper permissions
- Verify bucket name matches environment variable
- Check that files have content before upload (not empty)