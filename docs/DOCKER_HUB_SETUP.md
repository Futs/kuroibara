# Docker Hub Integration Setup

This document explains how to set up the Docker Hub integration for automatic image publishing.

## Overview

The Docker Hub workflow (`docker-hub.yml`) automatically builds and pushes Docker images to Docker Hub when:

1. **Main Branch**: Tests pass on the main branch
2. **Releases**: A new release is created or tagged
3. **Tags**: Version tags are pushed (e.g., `v1.0.0`)

## Required Setup

### 1. GitHub Environments

The workflow uses GitHub environments for deployment control:

- **staging**: Used for main branch builds
- **production**: Used for release builds

### 2. Environment Secrets

You need to configure the Docker Hub password in both environments:

#### DOCKER_PASSWORD
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

### Step 2: Set Up GitHub Environments

1. Go to your GitHub repository
2. Navigate to **Settings** → **Environments**
3. Create two environments:

#### Create Staging Environment
1. Click **New environment**
2. Name: `staging`
3. Add environment secret:
   - **Name**: `DOCKER_PASSWORD`
   - **Value**: Your Docker Hub access token

#### Create Production Environment
1. Click **New environment**
2. Name: `production`
3. **Optional**: Add protection rules (require reviews, restrict to main branch)
4. Add environment secret:
   - **Name**: `DOCKER_PASSWORD`
   - **Value**: Your Docker Hub access token

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

## Workflow Triggers & Environments

### Main Branch Push (Staging Environment)
```bash
git push origin main
```
- Waits for CI tests to pass
- Uses **staging** environment
- Builds and pushes images with `latest` tag
- Uses current version from `version.sh`

### Release Creation (Production Environment)
```bash
git tag v1.0.0
git push origin v1.0.0
```
- Uses **production** environment
- May require manual approval (if configured)
- Builds and pushes images immediately
- Tags with version number and `latest`

### GitHub Release (Production Environment)
- Triggered when a release is published through GitHub UI
- Uses **production** environment
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

## Environment Protection Rules (Optional)

For additional security, you can configure protection rules for the production environment:

### Recommended Production Environment Rules
1. **Required reviewers**: Require manual approval before deployment
2. **Deployment branches**: Restrict to `main` branch and release tags
3. **Wait timer**: Add a delay before deployment
4. **Environment secrets**: Store sensitive credentials securely

### Setting Up Protection Rules
1. Go to **Settings** → **Environments** → **production**
2. Enable **Required reviewers** and add team members
3. Enable **Deployment branches** and select "Selected branches"
4. Add branch rules for `main` and `refs/tags/v*`

This ensures that production Docker images are only built after proper review and approval.
