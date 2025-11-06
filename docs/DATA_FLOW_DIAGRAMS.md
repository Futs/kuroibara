# Kuroibara Data Flow Diagrams

This document provides detailed data flow diagrams showing how information moves through the Kuroibara system for different user scenarios.

## Table of Contents

1. [Search Flow](#search-flow)
2. [Library Management Flow](#library-management-flow)
3. [Download Flow](#download-flow)
4. [Health Monitoring Flow](#health-monitoring-flow)

---

## Search Flow

### Enhanced Search Data Flow

```mermaid
flowchart TD
    %% User Input
    A[User enters search query] --> B[Frontend validates input]
    B --> C[Send to Enhanced Search API]
    
    %% Backend Processing
    C --> D{Check cache first}
    D -->|Cache hit| E[Return cached results]
    D -->|Cache miss| F[Initiate tiered search]
    
    %% Tier 1: MangaUpdates
    F --> G[Query MangaUpdates API]
    G --> H{MangaUpdates healthy?}
    H -->|Yes| I[Parse MU response]
    H -->|No| J[Skip to Tier 2]
    I --> K[Enhance with metadata]
    
    %% Tier 2: MadaraDex
    J --> L[Query MadaraDex]
    K --> M{Sufficient results?}
    M -->|No| L
    L --> N{MadaraDex healthy?}
    N -->|Yes| O[Parse HTML response]
    N -->|No| P[Skip to Tier 3]
    O --> Q[Extract metadata]
    
    %% Tier 3: MangaDx
    P --> R[Query MangaDx API]
    Q --> S{Sufficient results?}
    S -->|No| R
    R --> T{MangaDx healthy?}
    T -->|Yes| U[Parse API response]
    T -->|No| V[Return available results]
    U --> W[Normalize data]
    
    %% Result Processing
    K --> X[Combine all results]
    Q --> X
    W --> X
    V --> X
    X --> Y[Remove duplicates]
    Y --> Z[Apply NSFW detection]
    Z --> AA[Cache results]
    AA --> BB[Return to frontend]
    E --> BB
    
    %% Frontend Display
    BB --> CC[Update search results grid]
    CC --> DD[Display manga cards]
    DD --> EE[User can view details/add to library]
    
    classDef userAction fill:#e3f2fd
    classDef processing fill:#f1f8e9
    classDef external fill:#fff3e0
    classDef result fill:#fce4ec
    
    class A,EE userAction
    class B,C,D,F,X,Y,Z,AA processing
    class G,L,R external
    class CC,DD,BB result
```

---

## Library Management Flow

### Add to Library Data Flow

```mermaid
flowchart TD
    %% User Action
    A[User clicks 'Add to Library'] --> B[Frontend validates selection]
    B --> C[Send to Library API]
    
    %% Backend Processing
    C --> D{Manga already in library?}
    D -->|Yes| E[Return existing entry]
    D -->|No| F[Create new manga entry]
    
    %% Metadata Processing
    F --> G[Extract metadata from search result]
    G --> H[Validate required fields]
    H --> I{Valid metadata?}
    I -->|No| J[Return validation error]
    I -->|Yes| K[Create MangaUpdates mapping]
    
    %% Database Operations
    K --> L[Begin database transaction]
    L --> M[Insert manga record]
    M --> N[Insert MangaUpdates entry]
    N --> O[Create mapping relationship]
    O --> P[Commit transaction]
    P --> Q[Update search cache]
    
    %% Response
    Q --> R[Return success response]
    E --> R
    J --> S[Return error response]
    R --> T[Frontend updates UI]
    S --> T
    T --> U[Show success/error message]
    U --> V[Refresh library if needed]
    
    classDef userAction fill:#e3f2fd
    classDef validation fill:#f1f8e9
    classDef database fill:#fff3e0
    classDef response fill:#fce4ec
    
    class A,V userAction
    class B,C,H,I validation
    class L,M,N,O,P database
    class R,S,T,U response
```

---

## Download Flow

### Torrent Download Data Flow

```mermaid
flowchart TD
    %% User Initiation
    A[User searches for torrents] --> B[Frontend calls Torrent API]
    B --> C[Torrent Indexer Service]
    
    %% Torrent Search
    C --> D[Query Nyaa.si]
    D --> E[Parse HTML results]
    E --> F[Extract torrent metadata]
    F --> G[Return torrent list]
    
    %% User Selection
    G --> H[User selects torrent]
    H --> I[Frontend sends download request]
    I --> J[Validate download client]
    
    %% Download Initiation
    J --> K{Client available?}
    K -->|No| L[Return client error]
    K -->|Yes| M[Create download record]
    M --> N[Add to download client]
    
    %% Client Communication
    N --> O{Magnet or torrent file?}
    O -->|Magnet| P[Send magnet to qBittorrent]
    O -->|File| Q[Download torrent file]
    Q --> R[Send file to qBittorrent]
    P --> S[Client starts download]
    R --> S
    
    %% Progress Tracking
    S --> T[Update download status]
    T --> U[Store in database]
    U --> V[Send WebSocket update]
    V --> W[Frontend updates progress]
    
    %% Completion Handling
    W --> X{Download complete?}
    X -->|No| Y[Continue monitoring]
    Y --> T
    X -->|Yes| Z[Post-processing]
    Z --> AA[File organization]
    AA --> BB[Update library]
    BB --> CC[Notify user]
    
    classDef userAction fill:#e3f2fd
    classDef torrentOps fill:#f1f8e9
    classDef clientOps fill:#fff3e0
    classDef monitoring fill:#fce4ec
    
    class A,H,CC userAction
    class C,D,E,F torrentOps
    class N,O,P,Q,R,S clientOps
    class T,U,V,W,X,Y monitoring
```

---

## Health Monitoring Flow

### System Health Check Data Flow

```mermaid
flowchart TD
    %% Monitoring Initiation
    A[Health check triggered] --> B{Manual or automatic?}
    B -->|Manual| C[User requests health check]
    B -->|Automatic| D[Scheduled background task]
    
    %% Health Check Execution
    C --> E[Health Monitoring Service]
    D --> E
    E --> F[Check database connection]
    E --> G[Check cache connection]
    E --> H[Check indexer health]
    E --> I[Check download clients]
    
    %% Database Health
    F --> J{Database responsive?}
    J -->|Yes| K[Record response time]
    J -->|No| L[Mark as unhealthy]
    
    %% Cache Health
    G --> M{Cache responsive?}
    M -->|Yes| N[Record cache stats]
    M -->|No| O[Mark as degraded]
    
    %% Indexer Health
    H --> P[Test MangaUpdates API]
    H --> Q[Test MadaraDex scraping]
    H --> R[Test MangaDx API]
    P --> S{MU responsive?}
    Q --> T{MDX responsive?}
    R --> U{MD responsive?}
    
    %% Client Health
    I --> V[Test qBittorrent API]
    I --> W[Test SABnzbd API]
    V --> X{qBittorrent responsive?}
    W --> Y{SABnzbd responsive?}
    
    %% Result Aggregation
    K --> Z[Aggregate health results]
    L --> Z
    N --> Z
    O --> Z
    S --> Z
    T --> Z
    U --> Z
    X --> Z
    Y --> Z
    
    %% Health Status Calculation
    Z --> AA[Calculate overall health]
    AA --> BB{All systems healthy?}
    BB -->|Yes| CC[Status: Healthy]
    BB -->|Some issues| DD[Status: Degraded]
    BB -->|Major issues| EE[Status: Unhealthy]
    
    %% Response and Caching
    CC --> FF[Cache health status]
    DD --> FF
    EE --> FF
    FF --> GG[Return health report]
    GG --> HH[Update monitoring dashboard]
    HH --> II[Send alerts if needed]
    
    classDef trigger fill:#e3f2fd
    classDef checking fill:#f1f8e9
    classDef evaluation fill:#fff3e0
    classDef response fill:#fce4ec
    
    class A,B,C,D trigger
    class E,F,G,H,I,P,Q,R,V,W checking
    class J,M,S,T,U,X,Y,AA,BB evaluation
    class FF,GG,HH,II response
```

---

## Data Flow Patterns

### Common Patterns Used Throughout Kuroibara

1. **Request-Response Pattern**: Standard HTTP request/response cycle
2. **Event-Driven Pattern**: WebSocket updates for real-time data
3. **Cache-Aside Pattern**: Check cache first, populate on miss
4. **Circuit Breaker Pattern**: Fail fast when external services are down
5. **Retry Pattern**: Automatic retry with exponential backoff
6. **Bulkhead Pattern**: Isolate failures to prevent cascade effects

### Performance Optimizations

- **Lazy Loading**: Load data only when needed
- **Pagination**: Limit result sets for better performance
- **Debouncing**: Reduce API calls for rapid user input
- **Prefetching**: Load likely-needed data in advance
- **Connection Pooling**: Reuse database connections efficiently
