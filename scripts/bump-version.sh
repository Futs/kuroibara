#!/bin/bash

# Version Bumping Script for Kuroibara
# Usage: ./scripts/bump-version.sh <new_version>
# Example: ./scripts/bump-version.sh 0.8.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if version argument is provided
if [ $# -eq 0 ]; then
    print_error "No version specified!"
    echo "Usage: $0 <new_version>"
    echo "Example: $0 0.8.0"
    exit 1
fi

NEW_VERSION="$1"

# Validate version format (semantic versioning)
if ! [[ $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid version format! Use semantic versioning (e.g., 1.2.3)"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(cat VERSION | tr -d '\n')
print_status "Current version: $CURRENT_VERSION"
print_status "New version: $NEW_VERSION"

# Confirm the change
echo
read -p "Are you sure you want to bump version from $CURRENT_VERSION to $NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Version bump cancelled."
    exit 0
fi

print_status "Updating version in all files..."

# Update VERSION file
echo "$NEW_VERSION" > VERSION
print_success "Updated VERSION file"

# Update backend files
sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" backend/app/__init__.py
print_success "Updated backend/app/__init__.py"

sed -i "s/version=\".*\"/version=\"$NEW_VERSION\"/" backend/app/main.py
print_success "Updated backend/app/main.py"

sed -i "0,/version = \".*\"/{s/version = \".*\"/version = \"$NEW_VERSION\"/}" backend/pyproject.toml
print_success "Updated backend/pyproject.toml"

# Update frontend files
sed -i "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" frontend/app/package.json
print_success "Updated frontend/app/package.json"

# Update docker-compose files if they exist
if [ -f "docker-compose.yml" ]; then
    sed -i "s/:v[0-9]\+\.[0-9]\+\.[0-9]\+/:v$NEW_VERSION/g" docker-compose.yml
    print_success "Updated docker-compose.yml"
fi

if [ -f "docker-compose.dev.yml" ]; then
    sed -i "s/:v[0-9]\+\.[0-9]\+\.[0-9]\+/:v$NEW_VERSION/g" docker-compose.dev.yml
    print_success "Updated docker-compose.dev.yml"
fi

print_status "Verifying changes..."

# Verify all files were updated
echo
print_status "Version references found:"
echo "VERSION file: $(cat VERSION)"
echo "Backend __init__.py: $(grep '__version__' backend/app/__init__.py)"
echo "Backend main.py: $(grep 'version=' backend/app/main.py)"
echo "Backend pyproject.toml: $(grep 'version =' backend/pyproject.toml)"
echo "Frontend package.json: $(grep '"version"' frontend/app/package.json)"

echo
print_success "Version bump completed successfully!"
print_status "Next steps:"
echo "1. Review the changes: git diff"
echo "2. Commit the changes: git add . && git commit -m 'bump: version $NEW_VERSION'"
echo "3. Create and push tag: git tag v$NEW_VERSION && git push origin v$NEW_VERSION"
echo "4. Push changes: git push origin main"
