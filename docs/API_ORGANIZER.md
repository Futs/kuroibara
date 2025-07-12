# Organizer API Reference

This document provides a comprehensive reference for the Kuroibara manga organizer API endpoints.

## Base URL

All organizer endpoints are prefixed with `/api/v1/organizer`

## Authentication

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Naming Format Management

### Validate Naming Format

Validate a naming format template for syntax and safety.

**Endpoint:** `POST /validate-naming-format`

**Request Body:**
```json
{
  "template": "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
}
```

**Response:**
```json
{
  "is_valid": true,
  "error_message": null,
  "sample_output": "Sample Manga/Volume 1/1 - Sample Chapter"
}
```

### Get Naming Settings

Retrieve current user's naming settings.

**Endpoint:** `GET /naming-settings`

**Response:**
```json
{
  "naming_format_manga": "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}",
  "naming_format_chapter": "{Chapter Number} - {Chapter Name}",
  "auto_organize_imports": true,
  "create_cbz_files": true,
  "preserve_original_files": false
}
```

### Update Naming Settings

Update user's naming settings.

**Endpoint:** `PUT /naming-settings`

**Request Body:**
```json
{
  "naming_format_manga": "{Manga Title}/Volume {Volume}",
  "naming_format_chapter": "{Chapter Number} - {Chapter Name}",
  "auto_organize_imports": true,
  "create_cbz_files": true,
  "preserve_original_files": false
}
```

**Response:** Same as GET naming-settings

## Organization Operations

### Organize Single Chapter

Organize a single chapter according to user's naming preferences.

**Endpoint:** `POST /organize/chapter`

**Request Body:**
```json
{
  "chapter_id": "550e8400-e29b-41d4-a716-446655440000",
  "preserve_original": false,
  "custom_naming_format": "{Manga Title}/{Chapter Number}"
}
```

**Response:**
```json
{
  "success": true,
  "organized_files": ["/app/storage/manga/.../organized/Naruto/Volume 1/1 - Enter Sasuke!.cbz"],
  "created_directories": ["/app/storage/manga/.../organized/Naruto/Volume 1"],
  "errors": [],
  "warnings": []
}
```

### Organize Manga

Organize all chapters of a manga (background task).

**Endpoint:** `POST /organize/manga`

**Request Body:**
```json
{
  "manga_id": "550e8400-e29b-41d4-a716-446655440000",
  "preserve_original": false,
  "custom_naming_format": "{Manga Title}/Volume {Volume}"
}
```

**Response:**
```json
{
  "message": "Organization job started",
  "job_id": "660e8400-e29b-41d4-a716-446655440000",
  "total_chapters": 25
}
```

### Batch Organization

Organize multiple manga/chapters at once (background task).

**Endpoint:** `POST /organize/batch`

**Request Body:**
```json
{
  "manga_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "chapter_ids": ["770e8400-e29b-41d4-a716-446655440000"],
  "organize_all_library": false,
  "preserve_original": false,
  "custom_naming_format": "{Manga Title}/Volume {Volume}"
}
```

**Response:**
```json
{
  "message": "Batch organization job started",
  "job_id": "880e8400-e29b-41d4-a716-446655440000",
  "job_type": "organize_manga_batch",
  "total_items": 150
}
```

## Job Management

### Get Organization Jobs

Retrieve user's organization jobs with progress information.

**Endpoint:** `GET /jobs`

**Response:**
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440000",
    "job_type": "organize_manga_batch",
    "job_status": "running",
    "progress_percentage": 65.5,
    "total_items": 150,
    "processed_items": 98,
    "successful_items": 95,
    "failed_items": 3,
    "started_at": "2023-07-10T14:30:00Z",
    "completed_at": null,
    "estimated_completion": "2023-07-10T15:00:00Z"
  }
]
```

### Get Specific Job

Retrieve detailed information about a specific organization job.

**Endpoint:** `GET /jobs/{job_id}`

**Response:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "job_type": "organize_manga_batch",
  "job_status": "completed",
  "progress_percentage": 100.0,
  "total_items": 150,
  "processed_items": 150,
  "successful_items": 147,
  "failed_items": 3,
  "job_config": {
    "manga_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    "preserve_original": false
  },
  "started_at": "2023-07-10T14:30:00Z",
  "completed_at": "2023-07-10T14:55:00Z",
  "estimated_completion": null,
  "result_summary": {
    "total_chapters": 150,
    "successful_chapters": 147,
    "failed_chapters": 3,
    "errors": ["Chapter file not found: /path/to/missing.cbz"]
  },
  "error_log": {
    "errors": ["Detailed error messages..."]
  }
}
```

## Migration & Validation

### Scan Unorganized Manga

Scan for manga that haven't been organized yet.

**Endpoint:** `GET /migration/scan`

**Response:**
```json
[
  {
    "manga_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Unorganized Manga",
    "chapter_count": 25,
    "is_organized": false,
    "has_organized_files": false,
    "storage_path": "/app/storage/manga/550e8400-e29b-41d4-a716-446655440000",
    "chapters": [
      {
        "chapter_id": "770e8400-e29b-41d4-a716-446655440000",
        "number": "1",
        "title": "Chapter Title",
        "file_path": "/path/to/chapter.cbz",
        "validation": {
          "valid": true,
          "errors": [],
          "warnings": [],
          "file_count": 20,
          "total_size": 15728640
        }
      }
    ]
  }
]
```

### Get Migration Plan

Get a migration plan for organizing a specific manga.

**Endpoint:** `GET /migration/plan/{manga_id}`

**Response:**
```json
{
  "manga_id": "550e8400-e29b-41d4-a716-446655440000",
  "valid": true,
  "errors": [],
  "warnings": [],
  "operations": [
    {
      "type": "organize_chapter",
      "chapter_id": "770e8400-e29b-41d4-a716-446655440000",
      "chapter_number": "1",
      "source_path": "/path/to/source.cbz",
      "target_path": "/app/storage/.../organized/Manga/Volume 1/1 - Chapter.cbz",
      "target_dir": "/app/storage/.../organized/Manga/Volume 1",
      "file_size": 15728640,
      "file_count": 20,
      "needs_cbz_conversion": false,
      "preserve_original": false
    }
  ],
  "estimated_size": 157286400,
  "estimated_duration": 45.5
}
```

### Validate Organization

Validate that a manga's organized structure is correct.

**Endpoint:** `GET /validation/{manga_id}`

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "organized_chapters": 25,
  "missing_chapters": [],
  "extra_files": []
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Rate Limiting

Organization operations, especially batch operations, may be rate-limited to prevent system overload. Large operations are automatically queued as background jobs.

## Storage Recovery

### Scan Storage for Recovery

Scan storage for manga that exist in files but not in database.

**Endpoint:** `GET /recovery/scan-storage`

**Response:**
```json
[
  {
    "storage_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "extracted_title": "Naruto",
    "chapter_count": 25,
    "volume_count": 3,
    "storage_size": 524288000,
    "has_volume_structure": true,
    "organized_path": "/app/storage/manga/.../organized",
    "volumes": {
      "Volume 1": [
        {
          "number": "1",
          "title": "Enter Sasuke!",
          "filename": "1 - Enter Sasuke!.cbz",
          "file_path": "/path/to/file.cbz"
        }
      ]
    },
    "metadata": {
      "description": "Extracted from CBZ metadata",
      "year": 2023,
      "status": "ongoing",
      "type": "manga",
      "provider": "mangadex",
      "external_id": "abc123"
    }
  }
]
```

### Recover Single Manga

Recover specific manga from storage into database.

**Endpoint:** `POST /recovery/recover-manga`

**Request Body:**
```json
{
  "storage_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "manga_title": "Naruto",
  "custom_metadata": {
    "description": "Custom description override"
  }
}
```

**Response:**
```json
{
  "success": true,
  "manga_id": "660e8400-e29b-41d4-a716-446655440000",
  "message": "Successfully recovered manga 'Naruto' with 25 chapters",
  "chapters_recovered": 25,
  "errors": []
}
```

### Batch Recovery

Recover multiple manga from storage in batch.

**Endpoint:** `POST /recovery/batch-recover`

**Request Body:**
```json
{
  "recovery_items": [
    {
      "storage_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "manga_title": "Naruto",
      "custom_metadata": null
    },
    {
      "storage_uuid": "770e8400-e29b-41d4-a716-446655440000",
      "manga_title": "One Piece",
      "custom_metadata": null
    }
  ],
  "skip_errors": true
}
```

**Response:**
```json
{
  "total_requested": 2,
  "successful_recoveries": 2,
  "failed_recoveries": 0,
  "recovered_manga": [
    {
      "success": true,
      "manga_id": "660e8400-e29b-41d4-a716-446655440000",
      "message": "Successfully recovered 'Naruto' with 25 chapters",
      "chapters_recovered": 25,
      "errors": []
    },
    {
      "success": true,
      "manga_id": "880e8400-e29b-41d4-a716-446655440000",
      "message": "Successfully recovered 'One Piece' with 150 chapters",
      "chapters_recovered": 150,
      "errors": []
    }
  ],
  "errors": []
}
```

## WebSocket Updates (Future)

For real-time progress updates on organization jobs, WebSocket connections will be available at:
```
ws://localhost:8000/ws/organizer/jobs/{job_id}
```

This will provide real-time updates on job progress, completion, and errors.
