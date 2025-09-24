# Database Migration Recommendation for Upload Persistence

## Current Setup Issues

Currently, upload metadata is stored in a JSON file (`user_uploads_store.json`), which has several problems:

1. **Data Loss on Redeploy**: When Railway redeploys, the JSON file is lost unless it's in a persistent volume
2. **Concurrency Issues**: Multiple requests could corrupt the JSON file
3. **No ACID Properties**: No transactions, rollback, or data integrity guarantees
4. **Limited Querying**: Can't efficiently search or filter uploads
5. **No Backup**: JSON file isn't included in database backups

## Recommendation: YES, Migrate to PostgreSQL

### Benefits:
1. **Persistence**: Data survives deployments and container restarts
2. **ACID Compliance**: Transactions ensure data integrity
3. **Scalability**: Can handle concurrent uploads without file locking issues
4. **Querying**: Can use SQL to search, filter, and aggregate upload data
5. **Relationships**: Can properly link uploads to users and organizations
6. **Backup/Recovery**: Included in database backup strategies

## Implementation Plan

### Option 1: Use Existing Document Model (Recommended)
The `Document` model already exists and has most fields we need:
- `user_id`, `organization_id` for ownership
- `filename`, `file_key`, `file_size` for file metadata
- `uploaded_at`, `status` for tracking
- `sha256` for file integrity

**Changes needed**:
1. Add migration to ensure Document table exists
2. Update upload endpoints to create Document records instead of JSON entries
3. Update list endpoints to query Document table

### Option 2: Create Dedicated Upload Model
Create a simpler `Upload` model if Document is too complex:
```python
class Upload(Base):
    __tablename__ = 'uploads'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_key = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    fingerprint = Column(String(32))
    doc_type = Column(String(100))
    standards_mapped = Column(JSON)  # PostgreSQL JSON column
    uploaded_at = Column(DateTime, default=datetime.utcnow)
```

## Migration Steps

1. **Create Database Migration**:
   ```python
   # In apply_upload_migration.py
   - Create uploads table or ensure documents table exists
   - Migrate existing JSON data to database
   ```

2. **Update Backend Code**:
   - Modify `_record_user_upload` to create database records
   - Update `_get_user_uploads` to query database
   - Remove JSON file operations

3. **Deployment**:
   - Deploy backend with migration
   - Run migration script
   - Verify uploads persist across deployments

## Environment Variables

The AWS S3 variables should remain as environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET_NAME`

These are configuration, not data, so environment variables are appropriate.

## Immediate Fix (Without Migration)

If you need a quick fix without database migration:
1. Mount a persistent volume in Railway for the JSON file
2. Set `USER_UPLOADS_STORE` to a path in the persistent volume
3. This provides persistence but doesn't solve other issues

## Conclusion

**Strongly recommend** migrating upload metadata to PostgreSQL for reliability, scalability, and proper data management. The Document model already exists and can be used immediately.