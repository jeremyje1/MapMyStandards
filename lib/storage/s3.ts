import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';

// Environment configuration with sensible fallbacks
const region = process.env.S3_REGION || process.env.AWS_REGION || 'us-east-1';
const endpoint = process.env.S3_ENDPOINT; // support R2/MinIO style endpoints
const accessKeyId = process.env.S3_ACCESS_KEY || process.env.AWS_ACCESS_KEY_ID;
const secretAccessKey = process.env.S3_SECRET_KEY || process.env.AWS_SECRET_ACCESS_KEY;
const bucket = process.env.S3_BUCKET || process.env.S3_BUCKET_NAME || '';

export const s3 = new S3Client({
  region,
  endpoint: endpoint || undefined,
  forcePathStyle: !!endpoint,
  credentials: accessKeyId && secretAccessKey ? { accessKeyId, secretAccessKey } : undefined,
});

export async function putObject(key: string, body: Buffer | Uint8Array | string, contentType: string) {
  if (!bucket) throw new Error('S3_BUCKET not configured');
  await s3.send(new PutObjectCommand({
    Bucket: bucket,
    Key: key,
    Body: body,
    ContentType: contentType,
    ServerSideEncryption: 'AES256',
  }));
  return { bucket, key };
}

export async function getObject(key: string) {
  if (!bucket) throw new Error('S3_BUCKET not configured');
  const res = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
  // Caller can handle stream/Buffer conversion as needed
  return res.Body as any;
}
