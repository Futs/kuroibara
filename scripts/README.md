# Kuroibara Scripts

This directory contains utility scripts for testing, configuration, and maintenance of the Kuroibara manga reader application.

## Provider Testing Scripts

### `test_providers.py`
**Comprehensive Provider Testing Suite**

A complete testing framework that systematically tests all manga providers for:
- Search functionality
- Manga details retrieval
- Chapter listing
- Page extraction (download capability)
- Library integration

**Usage:**
```bash
docker compose -f docker-compose.dev.yml exec backend python scripts/test_providers.py
```

**Features:**
- Tests 19+ providers (skips problematic ones)
- Timeout handling for slow providers
- Detailed error reporting
- Success rate analysis
- Automatic manga addition to library for testing

**Output:**
- Detailed test results for each provider
- Summary report with working/partially working/broken providers
- Success rate statistics

### `quick_provider_test.py`
**Fast Provider Testing**

A lightweight script for quick testing of priority providers without full workflow testing.

**Usage:**
```bash
docker compose -f docker-compose.dev.yml exec backend python scripts/quick_provider_test.py
```

**Features:**
- Tests priority providers first
- Faster execution (no library integration)
- Basic functionality verification

### `test_provider.py`
**Single Provider Testing**

Script for testing individual providers in detail.

## Configuration Scripts

### `generate_provider_config.py`
**Provider Configuration Generator**

Generates configuration files for manga providers.

### `test_template_system.py`
**Template System Testing**

Tests the provider template system functionality.

## Running Scripts

All scripts should be run from within the Docker backend container:

```bash
# General pattern
docker compose -f docker-compose.dev.yml exec backend python scripts/<script_name>.py

# Examples
docker compose -f docker-compose.dev.yml exec backend python scripts/test_providers.py
docker compose -f docker-compose.dev.yml exec backend python scripts/quick_provider_test.py
```

## Script Dependencies

Scripts require:
- Active Docker environment
- Database connection
- Provider registry
- User account in database

## Test Results Interpretation

### Provider Status Levels:
- **✅ Fully Working**: Search, details, chapters, and pages all work
- **⚠️ Partially Working**: Some functionality works (usually search + details)
- **❌ Not Working**: Basic search functionality fails

### Common Issues:
- **Cloudflare Protection**: Sites blocking automated access
- **Selector Issues**: Outdated CSS selectors for scraping
- **404/403 Errors**: Changed URLs or access restrictions
- **Page Extraction**: Returns logos/junk instead of manga pages

## Maintenance

Scripts should be updated when:
- New providers are added
- Provider configurations change
- Testing requirements evolve
- Bug fixes are needed

## Contributing

When adding new scripts:
1. Follow the existing naming convention
2. Add documentation to this README
3. Include usage examples
4. Add error handling and timeouts
5. Provide clear output formatting
