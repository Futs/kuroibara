# Manga Organizer & Naming System

The Kuroibara manga organizer provides a comprehensive system for organizing manga files according to customizable naming conventions, similar to the *arr suite of applications (Sonarr, Radarr, etc.).

## Overview

The organizer system consists of several key components:

1. **Naming Format Engine** - Flexible template system for file/folder naming
2. **File Organization Service** - Handles physical file operations
3. **CBZ Conversion Service** - Converts chapters to standardized CBZ format
4. **Batch Operations** - Process multiple manga/chapters efficiently
5. **Migration Tools** - Migrate existing libraries to new organization

## Naming Format System

### Template Variables

The naming system supports the following template variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{Manga Title}` | Sanitized manga title | `Naruto` |
| `{Volume}` | Volume number (with fallback) | `1`, `2`, `Special` |
| `{Chapter Number}` | Chapter number (supports decimals) | `1`, `12.5`, `Extra` |
| `{Chapter Name}` | Chapter title | `Enter Sasuke!` |
| `{Language}` | Language code | `en`, `jp`, `es` |
| `{Year}` | Publication year | `2023` |
| `{Source}` | Source provider | `mangadex`, `mangaplus` |

### Default Templates

**Manga Folder Structure:**
```
{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}
```

**Chapter File Naming:**
```
{Chapter Number} - {Chapter Name}
```

### Example Output

With the default templates, a chapter would be organized as:
```
/app/storage/manga/{manga-uuid}/organized/
├── Naruto/
│   ├── Volume 1/
│   │   ├── 1 - Enter Sasuke!.cbz
│   │   ├── 2 - The Worst Client.cbz
│   │   └── 3 - For the Sake of Dreams!.cbz
│   └── Volume 2/
│       ├── 4 - The Next Level!.cbz
│       └── 5 - You Failed!.cbz
```

## File Organization Structure

### Storage Layout

```
/app/storage/manga/{manga-uuid}/
├── organized/          # Organized files following naming conventions
│   └── {Manga Title}/
│       └── Volume {Volume}/
│           └── {Chapter Number} - {Chapter Name}.cbz
├── raw/               # Original files (if preserved)
│   └── original_files...
└── cover.jpg          # Manga cover image
```

### Organization Options

- **Auto-organize imports**: Automatically organize files when importing
- **Create CBZ files**: Convert chapters to CBZ format for better compatibility
- **Preserve original files**: Keep original files after organization (uses more storage)

## API Endpoints

### Naming Settings

#### Get Naming Settings
```http
GET /api/v1/organizer/naming-settings
```

#### Update Naming Settings
```http
PUT /api/v1/organizer/naming-settings
Content-Type: application/json

{
  "naming_format_manga": "{Manga Title}/Volume {Volume}",
  "naming_format_chapter": "{Chapter Number} - {Chapter Name}",
  "auto_organize_imports": true,
  "create_cbz_files": true,
  "preserve_original_files": false
}
```

#### Validate Naming Format
```http
POST /api/v1/organizer/validate-naming-format
Content-Type: application/json

{
  "template": "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
}
```

### Organization Operations

#### Organize Single Chapter
```http
POST /api/v1/organizer/organize/chapter
Content-Type: application/json

{
  "chapter_id": "uuid",
  "preserve_original": false,
  "custom_naming_format": "{Manga Title}/{Chapter Number}"
}
```

#### Organize Manga
```http
POST /api/v1/organizer/organize/manga
Content-Type: application/json

{
  "manga_id": "uuid",
  "preserve_original": false,
  "custom_naming_format": "{Manga Title}/Volume {Volume}"
}
```

#### Batch Organization
```http
POST /api/v1/organizer/organize/batch
Content-Type: application/json

{
  "manga_ids": ["uuid1", "uuid2"],
  "chapter_ids": ["uuid3", "uuid4"],
  "organize_all_library": false,
  "preserve_original": false,
  "custom_naming_format": "{Manga Title}/Volume {Volume}"
}
```

### Job Management

#### Get Organization Jobs
```http
GET /api/v1/organizer/jobs
```

#### Get Specific Job
```http
GET /api/v1/organizer/jobs/{job_id}
```

### Migration & Validation

#### Scan Unorganized Manga
```http
GET /api/v1/organizer/migration/scan
```

#### Get Migration Plan
```http
GET /api/v1/organizer/migration/plan/{manga_id}
```

#### Validate Organization
```http
GET /api/v1/organizer/validation/{manga_id}
```

## Database Models

### User Settings

New fields added to the `users` table:

```sql
naming_format_manga VARCHAR(500) DEFAULT '{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}'
naming_format_chapter VARCHAR(500) DEFAULT '{Chapter Number} - {Chapter Name}'
auto_organize_imports BOOLEAN DEFAULT TRUE
create_cbz_files BOOLEAN DEFAULT TRUE
preserve_original_files BOOLEAN DEFAULT FALSE
```

### Metadata Tracking

#### MangaMetadata
- `display_name`: Custom display name override
- `custom_cover_url`: Custom cover image URL
- `is_organized`: Whether manga is organized
- `organization_format`: Format used for organization
- `last_organized_at`: When last organized
- `reading_status`: Reading status (unread, reading, completed, dropped)

#### ChapterMetadata
- `display_name`: Custom chapter name override
- `is_organized`: Whether chapter is organized
- `organized_path`: Path after organization
- `original_path`: Original file path (if preserved)
- `cbz_path`: Path to CBZ file
- `current_page`: Current reading page
- `reading_progress`: Progress percentage (0-100)

#### OrganizationHistory
- `operation_type`: Type of operation (organize, rename, convert_cbz)
- `operation_status`: Status (success, failed, partial)
- `source_path`: Original file/directory path
- `destination_path`: New file/directory path
- `naming_format_used`: Naming format used
- `files_processed`: Number of files processed

#### OrganizationJob
- `job_type`: Type of job (organize_manga, organize_library, etc.)
- `job_status`: Status (pending, running, completed, failed, cancelled)
- `total_items`: Total items to process
- `processed_items`: Items processed so far
- `successful_items`: Successfully processed items
- `failed_items`: Failed items

## Frontend Integration

### Settings UI

The naming settings are integrated into the main Settings page with:

- **Manga Folder Structure**: Text input with live preview
- **Chapter File Naming**: Text input with live preview
- **Organization Options**: Toggle switches for auto-organize, CBZ creation, and file preservation
- **Template Validation**: Real-time validation with error messages

### Preview System

The frontend provides live previews of naming formats using sample data:
- Manga: "Naruto"
- Volume: "1"
- Chapter: "1 - Enter Sasuke!"

## Best Practices

### Naming Conventions

1. **Use consistent separators**: Stick to `-` for chapter names and `/` for folder separation
2. **Include volume information**: Helps with organization of long series
3. **Sanitize special characters**: The system automatically handles unsafe characters
4. **Consider sorting**: Use zero-padded numbers for proper sorting (handled automatically)

### File Organization

1. **Test naming formats**: Use the validation endpoint before applying to large libraries
2. **Backup important data**: Enable "preserve original files" for irreplaceable content
3. **Monitor organization jobs**: Check job status for large batch operations
4. **Validate after organization**: Use validation endpoints to ensure integrity

### Performance Considerations

1. **Batch operations**: Use batch endpoints for multiple manga/chapters
2. **Background processing**: Large operations run in background with progress tracking
3. **Storage space**: CBZ conversion and file preservation increase storage requirements
4. **Network impact**: Large reorganizations may impact system performance

## Troubleshooting

### Common Issues

1. **Invalid naming format**: Check template validation for syntax errors
2. **Missing files**: Use migration scan to identify unorganized content
3. **Permission errors**: Ensure proper file system permissions
4. **Storage space**: Monitor disk usage when preserving original files

### Error Recovery

1. **Failed organization jobs**: Check job error logs for specific issues
2. **Corrupted files**: Use validation tools to identify file integrity issues
3. **Incomplete migrations**: Use migration plans to resume interrupted operations

## Storage Recovery System

### Disaster Recovery

The storage recovery system helps recover manga when the database is lost but storage files remain intact.

#### When to Use Recovery

- Database corruption or complete loss
- Moving to a new server instance
- System crashes with storage backup available
- Migrating between different Kuroibara installations

#### Recovery Process

1. **Scan Storage**: Automatically detect organized manga in storage
   ```http
   GET /api/v1/organizer/recovery/scan-storage
   ```

2. **Review Recoverable Manga**: Examine found manga with extracted metadata
   - Manga titles from folder structure
   - Chapter counts and volume organization
   - Metadata from CBZ files (if available)

3. **Recover Individual or Batch**:
   ```http
   POST /api/v1/organizer/recovery/recover-manga
   POST /api/v1/organizer/recovery/batch-recover
   ```

#### What Gets Recovered

✅ **Preserved:**
- Manga titles and basic metadata
- Chapter organization and files
- Volume structure
- CBZ file metadata
- Organized file structure

❌ **Lost:**
- Reading progress and bookmarks
- Custom descriptions and tags
- User ratings and reviews
- Library categories and reading lists

#### Frontend Recovery Interface

Access via: **User Menu → Storage Recovery**

The recovery interface provides:
- **Storage Scanning**: One-click scan for recoverable manga
- **Detailed Preview**: View extracted metadata before recovery
- **Individual Recovery**: Recover specific manga
- **Batch Recovery**: Recover all found manga at once
- **Progress Tracking**: Monitor recovery operations

### Prevention and Best Practices

#### Automated Backup System

Kuroibara includes a comprehensive backup system with scheduled backups:

**Scheduled Backups:**
- **Daily**: Database-only backups at 2 AM (fast, metadata only)
- **Weekly**: Full backups on Sunday at 3 AM (includes storage files)
- **Monthly**: Archive backups on 1st day at 4 AM (long-term retention)

**Manual Backups:**
- Create on-demand backups via the web interface
- Choose database-only or full backup with storage
- Download backups directly from the browser

**Backup Contents:**
```
kuroibara_backup_20230710_140000.tar.gz
├── database.sql          # PostgreSQL dump
├── storage.tar.gz        # Storage files (if included)
└── backup_metadata.json  # Backup information
```

**API Endpoints:**
```bash
# List backups
GET /api/v1/backup/list

# Create backup
POST /api/v1/backup/create

# Download backup
GET /api/v1/backup/download/{filename}

# Upload and restore
POST /api/v1/backup/upload-restore
```

#### Docker Volume Management

```yaml
# docker-compose.yml - Use named volumes
volumes:
  kuroibara_storage:
    driver: local
  kuroibara_db:
    driver: local

services:
  backend:
    volumes:
      - kuroibara_storage:/app/storage
  postgres:
    volumes:
      - kuroibara_db:/var/lib/postgresql/data
```

## Migration from Existing Systems

### From Mango

The system can replace Mango's JSON-based metadata tracking with database storage:

1. **Scan existing library**: Use migration scan to identify current organization
2. **Create migration plan**: Generate plan for reorganization
3. **Execute migration**: Run batch organization with desired naming format
4. **Validate results**: Ensure all content is properly organized

### From Other Readers

1. **Import existing files**: Use the import system to add existing manga
2. **Apply organization**: Use batch operations to organize according to preferences
3. **Verify integrity**: Use validation tools to ensure proper organization

### After System Crashes

1. **Assess damage**: Determine what data is available (storage vs database)
2. **Use recovery tools**: If storage is intact, use the recovery system
3. **Restore from backups**: If available, restore both database and storage
4. **Re-import if necessary**: As last resort, re-import manga from original sources
