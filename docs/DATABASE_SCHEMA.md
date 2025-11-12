# Kuroibara Database Schema

This document provides a comprehensive overview of the Kuroibara database schema, including entity relationships, data flow, and design decisions.

## Database Overview

Kuroibara uses PostgreSQL as its primary database with the following design principles:
- **Normalized structure** to reduce data redundancy
- **Foreign key constraints** to maintain data integrity
- **Indexing strategy** for optimal query performance
- **JSON fields** for flexible metadata storage

---

## Entity Relationship Diagram

```mermaid
erDiagram
    %% Core User Management
    User {
        uuid id PK
        string email UK
        string username UK
        string hashed_password
        boolean is_active
        boolean is_superuser
        datetime created_at
        datetime updated_at
        json preferences
    }
    
    %% Manga Core Entity
    Manga {
        uuid id PK
        string title
        text description
        string cover_image_url
        string status
        string type
        integer year
        boolean is_nsfw
        datetime created_at
        datetime updated_at
        json metadata
        uuid user_id FK
    }
    
    %% MangaUpdates Integration
    MangaUpdatesEntry {
        uuid id PK
        bigint mu_series_id UK
        string title
        text description
        string image_url
        string url
        string type
        string year
        string status
        boolean is_nsfw
        json genres
        json authors
        json alternative_titles
        json categories
        float rating
        integer rating_votes
        datetime created_at
        datetime updated_at
        json raw_data
    }
    
    MangaUpdatesMapping {
        uuid id PK
        uuid manga_id FK
        uuid mangaupdates_entry_id FK
        float confidence_score
        string match_type
        datetime created_at
    }
    
    %% Chapter Management
    Chapter {
        uuid id PK
        uuid manga_id FK
        string title
        string chapter_number
        string volume_number
        string url
        string provider
        datetime release_date
        datetime created_at
        datetime updated_at
        json metadata
    }
    
    %% Download Management
    Download {
        uuid id PK
        string title
        uuid manga_id FK
        uuid user_id FK
        uuid client_id FK
        string download_type
        string status
        string external_id
        string external_url
        float progress
        bigint size_bytes
        bigint downloaded_bytes
        datetime started_at
        datetime completed_at
        datetime created_at
        datetime updated_at
        json metadata
    }
    
    DownloadClient {
        uuid id PK
        string name
        string client_type
        string host
        integer port
        string username
        string password
        boolean is_enabled
        boolean is_default
        datetime created_at
        datetime updated_at
        json settings
    }
    
    %% Provider Management
    Provider {
        uuid id PK
        string name
        string provider_type
        string base_url
        boolean is_enabled
        boolean is_nsfw
        integer priority
        datetime last_health_check
        string health_status
        json health_details
        datetime created_at
        datetime updated_at
        json settings
    }
    
    %% User Library Management
    UserManga {
        uuid id PK
        uuid user_id FK
        uuid manga_id FK
        string status
        float rating
        text notes
        datetime added_at
        datetime last_read_at
        datetime created_at
        datetime updated_at
    }
    
    %% Reading Progress
    ReadingProgress {
        uuid id PK
        uuid user_id FK
        uuid manga_id FK
        uuid chapter_id FK
        integer page_number
        integer total_pages
        boolean completed
        datetime read_at
        datetime created_at
        datetime updated_at
    }
    
    %% Categories and Tags
    Category {
        uuid id PK
        string name
        string description
        string color
        uuid user_id FK
        datetime created_at
        datetime updated_at
    }
    
    MangaCategory {
        uuid id PK
        uuid manga_id FK
        uuid category_id FK
        datetime created_at
    }
    
    %% Reading Lists
    ReadingList {
        uuid id PK
        string name
        text description
        boolean is_public
        uuid user_id FK
        datetime created_at
        datetime updated_at
    }
    
    ReadingListManga {
        uuid id PK
        uuid reading_list_id FK
        uuid manga_id FK
        integer order_index
        datetime added_at
    }
    
    %% Health Monitoring
    HealthCheck {
        uuid id PK
        string component_type
        string component_name
        string status
        float response_time_ms
        text message
        datetime checked_at
        json details
    }
    
    %% Relationships
    User ||--o{ Manga : "owns"
    User ||--o{ UserManga : "has"
    User ||--o{ ReadingProgress : "tracks"
    User ||--o{ Category : "creates"
    User ||--o{ ReadingList : "creates"
    User ||--o{ Download : "initiates"
    
    Manga ||--o{ Chapter : "contains"
    Manga ||--o{ UserManga : "belongs_to"
    Manga ||--o{ ReadingProgress : "tracked_in"
    Manga ||--o{ MangaCategory : "categorized_in"
    Manga ||--o{ ReadingListManga : "included_in"
    Manga ||--o{ Download : "downloaded_as"
    Manga ||--o{ MangaUpdatesMapping : "mapped_to"
    
    MangaUpdatesEntry ||--o{ MangaUpdatesMapping : "maps_to"
    
    Chapter ||--o{ ReadingProgress : "read_in"
    
    DownloadClient ||--o{ Download : "handles"
    
    Category ||--o{ MangaCategory : "contains"
    
    ReadingList ||--o{ ReadingListManga : "includes"
```

---

## Key Design Decisions

### 1. UUID Primary Keys
- **Benefit**: Globally unique identifiers, better for distributed systems
- **Trade-off**: Slightly larger storage footprint than integers
- **Use Case**: Enables easy data migration and external API integration

### 2. JSON Metadata Fields
- **Benefit**: Flexible schema for provider-specific data
- **Trade-off**: Less queryable than normalized columns
- **Use Case**: Store raw API responses and dynamic metadata

### 3. Soft Relationships
- **Benefit**: Maintains data integrity while allowing flexibility
- **Implementation**: Foreign keys with cascade options
- **Use Case**: User deletion doesn't orphan manga data

### 4. Audit Timestamps
- **Fields**: `created_at`, `updated_at` on all entities
- **Benefit**: Track data lifecycle and debugging
- **Implementation**: Automatic updates via SQLAlchemy events

---

## Indexing Strategy

### Primary Indexes
```sql
-- Performance-critical indexes
CREATE INDEX idx_manga_user_id ON manga(user_id);
CREATE INDEX idx_manga_title_search ON manga USING gin(to_tsvector('english', title));
CREATE INDEX idx_chapter_manga_id ON chapter(manga_id);
CREATE INDEX idx_download_user_status ON download(user_id, status);
CREATE INDEX idx_mangaupdates_series_id ON mangaupdates_entry(mu_series_id);

-- Composite indexes for common queries
CREATE INDEX idx_user_manga_status ON user_manga(user_id, status);
CREATE INDEX idx_reading_progress_user_manga ON reading_progress(user_id, manga_id);
CREATE INDEX idx_health_check_component_time ON health_check(component_type, checked_at);
```

### Search Optimization
```sql
-- Full-text search indexes
CREATE INDEX idx_manga_fulltext ON manga USING gin(
    to_tsvector('english', title || ' ' || coalesce(description, ''))
);

CREATE INDEX idx_mangaupdates_fulltext ON mangaupdates_entry USING gin(
    to_tsvector('english', title || ' ' || coalesce(description, ''))
);
```

---

## Data Integrity Constraints

### Foreign Key Constraints
- **Cascading Deletes**: User deletion cascades to user-specific data
- **Restrict Deletes**: Manga with chapters cannot be deleted
- **Set Null**: Provider deletion sets provider_id to null in chapters

### Check Constraints
```sql
-- Ensure valid status values
ALTER TABLE manga ADD CONSTRAINT manga_status_check 
    CHECK (status IN ('ongoing', 'completed', 'hiatus', 'cancelled'));

-- Ensure valid download progress
ALTER TABLE download ADD CONSTRAINT download_progress_check 
    CHECK (progress >= 0 AND progress <= 100);

-- Ensure valid ratings
ALTER TABLE user_manga ADD CONSTRAINT user_manga_rating_check 
    CHECK (rating >= 0 AND rating <= 10);
```

---

## Performance Considerations

### Query Optimization
1. **Eager Loading**: Use JOIN queries for related data
2. **Pagination**: Implement cursor-based pagination for large datasets
3. **Caching**: Cache frequently accessed manga metadata
4. **Connection Pooling**: Reuse database connections efficiently

### Storage Optimization
1. **Image URLs**: Store URLs, not binary data
2. **JSON Compression**: Use JSONB for better performance
3. **Archival Strategy**: Move old health checks to separate tables
4. **Vacuum Strategy**: Regular maintenance for optimal performance
