# Backup Directory

This directory stores database backups from the EC2 deployment.

## Backup Files
- `a3e_backup_YYYYMMDD_HHMMSS.sql` - PostgreSQL database dumps

## Usage
```bash
# Create backup
make manage-ec2 COMMAND=backup

# Restore backup (example)
psql -U a3e -d a3e < backups/a3e_backup_20250731_120000.sql
```

## Retention
- Keep at least 7 daily backups
- Keep at least 4 weekly backups  
- Keep at least 3 monthly backups
