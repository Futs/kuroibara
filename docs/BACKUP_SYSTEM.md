# Kuroibara Backup & Restore System

The Kuroibara backup system provides comprehensive data protection with automated scheduling, browser downloads, and complete restore capabilities.

## Overview

The backup system consists of:

1. **Automated Scheduled Backups** - Daily, weekly, and monthly backups
2. **Manual On-Demand Backups** - Create backups anytime via web interface
3. **Browser Downloads** - Download backups directly to your device
4. **Complete Restore** - Upload and restore from backup files
5. **Storage Recovery** - Recover from orphaned storage files

## Backup Types

### Database-Only Backups
- **Contents**: User accounts, manga metadata, reading progress, settings
- **Size**: Small (typically 1-10 MB)
- **Speed**: Fast (seconds to minutes)
- **Use Case**: Daily backups, quick metadata protection

### Full Backups
- **Contents**: Database + all manga files and storage
- **Size**: Large (depends on library size)
- **Speed**: Slower (minutes to hours)
- **Use Case**: Weekly/monthly backups, complete protection

## Scheduled Backup System

### Default Schedule

| Type | Frequency | Time | Contents | Retention |
|------|-----------|------|----------|-----------|
| Daily | Every day | 2:00 AM | Database only | 7 backups |
| Weekly | Sunday | 3:00 AM | Full backup | 4 backups |
| Monthly | 1st day | 4:00 AM | Full backup | 12 backups |

### Configuration

Backup scheduling is configured via environment variables:

```bash
# Enable/disable scheduled backups
BACKUP_DAILY_ENABLED=true
BACKUP_WEEKLY_ENABLED=true
BACKUP_MONTHLY_ENABLED=true

# Backup storage settings
BACKUP_PATH=/app/backups
MAX_BACKUPS=30
```

### Docker Volume Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    volumes:
      - storage_data:/app/storage
      - backup_data:/app/backups    # Backup volume
    environment:
      - BACKUP_PATH=/app/backups

volumes:
  storage_data:
  backup_data:                      # Persistent backup storage
```

## Manual Backup Operations

### Web Interface

Access via: **User Menu → Backup & Restore**

**Create Backup:**
1. Click "Create Backup"
2. Choose backup name (optional)
3. Select "Include storage files" for full backup
4. Click "Create Backup"

**Download Backup:**
1. Find backup in the list
2. Click "Download" button
3. File downloads to your browser's download folder

**Upload & Restore:**
1. Click "Upload & Restore"
2. Select backup file (.tar.gz)
3. Confirm overwrite warning
4. Upload begins restore process

### API Operations

#### Create Backup
```bash
curl -X POST "http://localhost:8000/api/v1/backup/create" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "backup_name": "manual_backup_20230710",
    "include_storage": true
  }'
```

#### List Backups
```bash
curl -X GET "http://localhost:8000/api/v1/backup/list" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

#### Download Backup
```bash
curl -X GET "http://localhost:8000/api/v1/backup/download/backup_20230710.tar.gz" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -o backup_20230710.tar.gz
```

#### Upload & Restore
```bash
curl -X POST "http://localhost:8000/api/v1/backup/upload-restore" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "backup_file=@backup_20230710.tar.gz"
```

## Backup File Structure

```
kuroibara_backup_20230710_140000.tar.gz
├── database.sql              # PostgreSQL database dump
├── storage.tar.gz            # Compressed storage files (if included)
└── backup_metadata.json      # Backup information
```

### Metadata Format
```json
{
  "backup_name": "weekly_20230710",
  "created_at": "2023-07-10T14:00:00.000Z",
  "kuroibara_version": "1.0.0",
  "includes_storage": true,
  "database_size": 5242880,
  "storage_size": 1073741824
}
```

## Restore Process

### Complete Restore Workflow

1. **Upload Backup**: Use web interface or API to upload backup file
2. **Automatic Extraction**: System extracts database and storage components
3. **Database Restore**: PostgreSQL database is restored from dump
4. **Storage Restore**: Storage files are extracted (if included)
5. **Verification**: System verifies restore completion

### Restore Scenarios

#### Scenario 1: Complete System Recovery
- **Situation**: Total system failure, new installation
- **Process**: Upload full backup → Complete restore
- **Result**: Exact replica of backed-up state

#### Scenario 2: Database Corruption
- **Situation**: Database issues, storage intact
- **Process**: Upload database-only backup → Database restore
- **Result**: Metadata restored, existing storage preserved

#### Scenario 3: Storage Loss
- **Situation**: Storage corruption, database intact
- **Process**: Use storage recovery tools + restore storage from backup
- **Result**: Files restored, metadata preserved

## Disaster Recovery Procedures

### Complete System Loss

1. **Deploy New Instance**
   ```bash
   docker-compose up -d
   ```

2. **Upload Backup**
   - Navigate to Backup & Restore page
   - Upload most recent full backup
   - Wait for restore completion

3. **Verify Recovery**
   - Check manga library
   - Verify reading progress
   - Test file access

### Partial Data Loss

1. **Assess Damage**
   - Check what data is available
   - Determine backup needs

2. **Selective Restore**
   - Database-only backup for metadata
   - Storage recovery for files
   - Manual recovery for specific items

3. **Validation**
   - Use validation tools
   - Check for orphaned files
   - Verify data integrity

## Best Practices

### Backup Strategy

1. **Multiple Backup Types**
   - Keep both database-only and full backups
   - Use different retention periods
   - Store backups in multiple locations

2. **Regular Downloads**
   - Download weekly/monthly backups
   - Store on external drives
   - Keep offsite copies

3. **Test Restores**
   - Periodically test restore procedures
   - Verify backup integrity
   - Practice disaster recovery

### Storage Management

1. **Monitor Backup Size**
   - Check backup storage usage
   - Clean up old backups regularly
   - Monitor disk space

2. **Backup Retention**
   - Adjust retention based on needs
   - Keep longer retention for monthly backups
   - Archive important backups separately

### Security Considerations

1. **Access Control**
   - Backup operations require authentication
   - Secure backup storage location
   - Protect backup files

2. **Data Privacy**
   - Backups contain all user data
   - Encrypt backups for sensitive data
   - Secure backup transmission

## Troubleshooting

### Common Issues

#### Backup Creation Fails
- **Check disk space** in backup directory
- **Verify database connectivity** for pg_dump
- **Check permissions** on backup directory

#### Restore Fails
- **Verify backup file integrity** (not corrupted)
- **Check database connectivity** for restore
- **Ensure sufficient disk space** for extraction

#### Scheduled Backups Not Running
- **Check scheduler status** in application logs
- **Verify backup settings** in configuration
- **Check system time** and timezone settings

### Log Analysis

```bash
# Check backup-related logs
docker logs kuroibara-backend | grep -i backup

# Check scheduler logs
docker logs kuroibara-backend | grep -i scheduler

# Check database logs
docker logs kuroibara-postgres
```

### Manual Recovery

If automated restore fails, manual recovery is possible:

```bash
# Extract backup manually
tar -xzf backup_20230710.tar.gz

# Restore database manually
psql -U kuroibara -d kuroibara < database.sql

# Extract storage manually
tar -xzf storage.tar.gz -C /app/
```

## Migration Between Instances

### Export from Source
1. Create full backup on source instance
2. Download backup file
3. Verify backup integrity

### Import to Destination
1. Deploy new Kuroibara instance
2. Upload backup file
3. Wait for restore completion
4. Verify migration success

### Post-Migration Checklist
- [ ] All manga appear in library
- [ ] Reading progress preserved
- [ ] User settings intact
- [ ] File access working
- [ ] Scheduled backups configured

## Monitoring and Maintenance

### Health Checks
- Monitor backup creation success/failure
- Check backup file sizes and growth
- Verify scheduled backup execution
- Test restore procedures periodically

### Maintenance Tasks
- Clean up old backups regularly
- Monitor backup storage usage
- Update backup retention policies
- Review and test disaster recovery procedures

The backup system provides comprehensive protection for your manga library with minimal manual intervention while offering complete control when needed.
