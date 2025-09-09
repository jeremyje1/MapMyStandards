#!/usr/bin/env python3
"""
Test S3 Setup for MapMyStandards
Run this after setting up AWS to verify everything works
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_s3_connection():
    """Test S3 bucket connection and permissions"""
    
    # Get credentials from environment or prompt
    access_key = os.getenv('AWS_ACCESS_KEY_ID') or input('Enter AWS Access Key ID: ')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') or input('Enter AWS Secret Access Key: ')
    region = os.getenv('AWS_REGION', 'us-east-1')
    bucket_name = os.getenv('S3_BUCKET') or input('Enter S3 Bucket Name: ')
    
    if not all([access_key, secret_key, bucket_name]):
        print("❌ Missing required credentials")
        return False
    
    # Create S3 client
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        print(f"✅ S3 client created successfully")
    except Exception as e:
        print(f"❌ Failed to create S3 client: {e}")
        return False
    
    # Test 1: List bucket (verify access)
    print("\n📋 Test 1: Checking bucket access...")
    try:
        response = s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' is accessible")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"❌ Bucket '{bucket_name}' not found")
        elif error_code == '403':
            print(f"❌ Access denied to bucket '{bucket_name}'")
        else:
            print(f"❌ Error accessing bucket: {e}")
        return False
    
    # Test 2: Generate presigned POST (for uploads)
    print("\n📤 Test 2: Testing presigned POST generation...")
    try:
        presigned_post = s3_client.generate_presigned_post(
            Bucket=bucket_name,
            Key='test/upload-test.txt',
            Fields={'Content-Type': 'text/plain'},
            Conditions=[
                {'Content-Type': 'text/plain'},
                ['content-length-range', 0, 10485760]  # 10MB max
            ],
            ExpiresIn=3600
        )
        print(f"✅ Presigned POST URL generated successfully")
        print(f"   URL: {presigned_post['url']}")
    except ClientError as e:
        print(f"❌ Failed to generate presigned POST: {e}")
        return False
    
    # Test 3: Generate presigned GET (for downloads)
    print("\n📥 Test 3: Testing presigned GET generation...")
    try:
        presigned_get = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': 'test/download-test.txt'},
            ExpiresIn=3600
        )
        print(f"✅ Presigned GET URL generated successfully")
    except ClientError as e:
        print(f"❌ Failed to generate presigned GET: {e}")
        return False
    
    # Test 4: Check CORS configuration
    print("\n🌐 Test 4: Checking CORS configuration...")
    try:
        cors = s3_client.get_bucket_cors(Bucket=bucket_name)
        print(f"✅ CORS is configured")
        for rule in cors['CORSRules']:
            print(f"   Allowed Origins: {rule.get('AllowedOrigins', [])}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
            print(f"⚠️  No CORS configuration found (you should add one)")
        else:
            print(f"❌ Error checking CORS: {e}")
    
    print("\n" + "="*50)
    print("🎉 S3 Setup Test Complete!")
    print("="*50)
    print("\n✅ Your S3 bucket is properly configured!")
    print("\n📝 Next steps:")
    print("1. Add these environment variables to Railway:")
    print(f"   AWS_ACCESS_KEY_ID={access_key[:10]}...")
    print(f"   AWS_SECRET_ACCESS_KEY=***")
    print(f"   AWS_REGION={region}")
    print(f"   S3_BUCKET={bucket_name}")
    print("   STORAGE_PROVIDER=aws")
    print("\n2. Redeploy your Railway service")
    print("3. Test file upload from your application")
    
    return True

if __name__ == "__main__":
    print("="*50)
    print("MapMyStandards S3 Setup Tester")
    print("="*50)
    
    success = test_s3_connection()
    
    if not success:
        print("\n❌ Some tests failed. Please check your AWS configuration.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed! Your S3 is ready to use.")
        sys.exit(0)