# Versioning Guide for Kuroibara

This project uses **Semantic Versioning (SemVer)** with a Feature → Dev → Main branching strategy.

**Current Version: 0.1.0** (Development Phase)

## Version Format

- **Production**: `0.1.0` (clean semantic version)
- **Development**: `0.1.0-dev.123+abc1234` (with build number and git hash)
- **Release Candidate**: `0.1.0-rc.1` (release candidate)
- **Pull Request**: `0.1.0-pr.456` (pull request builds)

## Branching Strategy

```
Feature Branch → Dev Branch → Main Branch → Production Tag
      ↓              ↓            ↓             ↓
   (PR build)    (dev build)  (release)   (production)
```

## Using the Version Script

The `version.sh` script handles all versioning operations:

### View Current Version
```bash
./version.sh current
```

### Bump Version (Dev Branch Only)
```bash
# Bump patch version (0.1.0 → 0.1.1)
./version.sh bump patch

# Bump minor version (0.1.0 → 0.2.0)
./version.sh bump minor

# Bump major version (0.1.0 → 1.0.0) - for first stable release
./version.sh bump major
```

### Generate Development Version
```bash
# Creates version like: 0.1.0-dev.27+5f0ea44
./version.sh dev
```

### Create Release Candidate
```bash
# Creates version like: 0.1.0-rc.1
./version.sh rc
```

### Create Release Version (Main Branch Only)
```bash
# Creates clean version like: 0.1.0
./version.sh release
```

### Create Git Tag
```bash
# Creates and tags current version
./version.sh tag
```

## Workflow Examples

### 1. Feature Development
```bash
# On feature branch
git checkout -b feature/new-manga-reader
# ... make changes ...
git commit -m "Add new manga reader component"

# Create PR to dev
git push origin feature/new-manga-reader
# GitHub Actions will run tests and build PR version
```

### 2. Development Release
```bash
# On dev branch
git checkout dev
git merge feature/new-manga-reader

# Bump version for new feature
./version.sh bump minor  # 0.1.0 → 0.2.0

# Commit and push
git add VERSION
git commit -m "Bump version to 0.2.0"
git push origin dev

# GitHub Actions will:
# - Run tests
# - Build images with dev version (0.2.0-dev.28+abc1234)
# - Deploy to staging
```

### 3. Production Release
```bash
# Promote dev to main
git checkout main
git merge dev

# Push to trigger production deployment
git push origin main

# GitHub Actions will:
# - Build production images (0.2.0)
# - Deploy to production

# Create release tag
git tag v0.2.0
git push origin v0.2.0

# GitHub Actions will:
# - Create GitHub release
# - Include changelog and docker image info
```

## Docker Images

Images are tagged with the generated version:

- **Development**: `ghcr.io/your-org/kuroibara-backend:0.1.0-dev.28+abc1234`
- **Production**: `ghcr.io/your-org/kuroibara-backend:0.1.0`

## Build Arguments

Docker images receive these build arguments:

- `VERSION`: The generated version string
- `BUILD_DATE`: Build timestamp
- `GIT_SHA`: Git commit hash

You can use these in your Dockerfile:
```dockerfile
ARG VERSION
ARG BUILD_DATE
ARG GIT_SHA

LABEL version=$VERSION \
      build-date=$BUILD_DATE \
      git-sha=$GIT_SHA
```

## Version Information in Applications

### Backend (Python)
```python
from app import __version__
print(f"Kuroibara Backend v{__version__}")  # v0.1.0
```

### Frontend (JavaScript)
```javascript
import { version } from '../package.json';
console.log(`Kuroibara Frontend v${version}`);  // v0.1.0
```

## CI/CD Integration

The GitHub Actions workflow automatically:

1. **Generates appropriate versions** based on branch/trigger
2. **Builds and tags Docker images** with version info
3. **Deploys to staging** (dev branch) or production (main/tags)
4. **Creates releases** with changelog and version info

## Best Practices

1. **Only bump versions on dev branch** - keeps main stable
2. **Use semantic versioning** - breaking changes = major, features = minor, fixes = patch
3. **Tag releases** - creates clean production releases
4. **Review staging** - test on staging before promoting to main
5. **Write good commit messages** - they appear in changelog

## Troubleshooting

### Version script not working?
```bash
# Make sure it's executable
chmod +x version.sh

# Check git repository state
git status
```

### Docker build failing?
```bash
# Check if version format is valid
./version.sh current

# Verify git state
git log --oneline -5
```

### GitHub Actions failing?
- Check if VERSION file exists
- Verify git history is available (`fetch-depth: 0`)
- Ensure proper permissions for package registry
