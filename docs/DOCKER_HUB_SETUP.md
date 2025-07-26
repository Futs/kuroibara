# Docker Hub Integration Setup

This document explains how to set up the Docker Hub integration for automatic image publishing.

## Overview

The Docker Hub workflow (`docker-hub.yml`) automatically builds and pushes Docker images to Docker Hub when:

1. **Main Branch**: Tests pass on the main branch
2. **Releases**: A new release is created or tagged
3. **Tags**: Version tags are pushed (e.g., `v1.0.0`)

## Required Secrets

You need to configure the following secret in your GitHub repository:

### DOCKER_PASSWORD
Your Docker Hub password or access token (recommended) for the `futs` organization.

**Note**: The Docker Hub username is hardcoded to `futs` in the workflow.

## Setting Up Secrets

### Step 1: Create Docker Hub Access Token (Recommended)

1. Go to [Docker Hub](https://hub.docker.com/)
2. Sign in to your account
3. Go to **Account Settings** → **Security**
4. Click **New Access Token**
5. Give it a name (e.g., "GitHub Actions")
6. Select appropriate permissions (Read, Write, Delete)
7. Copy the generated token

### Step 2: Add Secrets to GitHub Repository

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:

   **DOCKER_PASSWORD**
   ```
   your-dockerhub-access-token-or-password
   ```

## Docker Images

The workflow will create the following Docker images:

### Backend Image
- **Repository**: `futs/kuroibara-backend`
- **Tags**:
  - `latest` (from main branch)
  - Version number (e.g., `0.6.0`)
  - Git tag (e.g., `v0.6.0`)

### Frontend Image
- **Repository**: `futs/kuroibara-frontend`
- **Tags**:
  - `latest` (from main branch)
  - Version number (e.g., `0.6.0`)
  - Git tag (e.g., `v0.6.0`)

## Workflow Triggers

### Main Branch Push
```bash
git push origin main
```
- Waits for CI tests to pass
- Builds and pushes images with `latest` tag
- Uses current version from `version.sh`

### Release Creation
```bash
git tag v1.0.0
git push origin v1.0.0
```
- Builds and pushes images immediately
- Tags with version number and `latest`

### GitHub Release
- Triggered when a release is published through GitHub UI
- Uses release tag for versioning

## Usage Examples

### Pull Images
```bash
# Backend
docker pull futs/kuroibara-backend:latest
docker pull futs/kuroibara-backend:0.6.0

# Frontend
docker pull futs/kuroibara-frontend:latest
docker pull futs/kuroibara-frontend:0.6.0
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    image: futs/kuroibara-backend:latest
    # ... other configuration

  frontend:
    image: futs/kuroibara-frontend:latest
    # ... other configuration
```

## Troubleshooting

### Authentication Errors
- Verify Docker Hub credentials are correct
- Ensure access token has write permissions
- Check if 2FA is enabled (use access token instead of password)

### Build Failures
- Check Dockerfile syntax in `backend/Dockerfile` and `frontend/app/Dockerfile`
- Verify build context paths are correct
- Review GitHub Actions logs for detailed error messages

### Missing Dependencies
- Ensure all required files are present in build context
- Check `.dockerignore` files aren't excluding necessary files

## Security Notes

1. **Use Access Tokens**: Prefer Docker Hub access tokens over passwords
2. **Limit Permissions**: Give tokens only necessary permissions
3. **Rotate Regularly**: Update access tokens periodically
4. **Monitor Usage**: Check Docker Hub for unauthorized access

## Monitoring

You can monitor the workflow execution:

1. Go to **Actions** tab in your GitHub repository
2. Look for "Docker Hub Release" workflows
3. Check logs for build status and image details
4. Verify images appear in your Docker Hub repositories

## Integration with Existing Workflows

This workflow complements the existing `deploy.yml` workflow:

- `deploy.yml`: Uses GitHub Container Registry (ghcr.io)
- `docker-hub.yml`: Uses Docker Hub (docker.io)

Both can run simultaneously, providing multiple distribution channels for your images.
