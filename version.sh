#!/bin/bash

# Version management script for kuroibara
# Supports Feature -> Dev -> Main branching strategy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/VERSION"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  current                    Show current version"
    echo "  bump [major|minor|patch]   Bump version (dev branch only)"
    echo "  dev                        Create dev version (x.y.z-dev.build)"
    echo "  rc                         Create release candidate (x.y.z-rc.n)"
    echo "  release                    Create release version (main branch only)"
    echo "  tag                        Create git tag for current version"
    echo ""
    echo "Environment Variables:"
    echo "  QUIET=true                 Suppress colored output (for CI/CD)"
    echo ""
    echo "Examples:"
    echo "  $0 current"
    echo "  $0 bump patch"
    echo "  $0 dev"
    echo "  $0 rc"
    echo "  $0 release"
    echo "  QUIET=true $0 dev          # For CI/CD usage"
}

get_current_version() {
    if [[ -f "$VERSION_FILE" ]]; then
        cat "$VERSION_FILE"
    else
        echo "0.1.0"
    fi
}

get_build_number() {
    # Use git commit count as build number
    git rev-list --count HEAD
}

get_git_hash() {
    git rev-parse --short HEAD
}

bump_version() {
    local bump_type=$1
    local current_version=$(get_current_version)
    
    if [[ "$CURRENT_BRANCH" != "dev" ]]; then
        echo -e "${RED}Error: Version bumping only allowed on dev branch${NC}"
        exit 1
    fi
    
    # Parse semantic version
    if [[ $current_version =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(-.*)?$ ]]; then
        major=${BASH_REMATCH[1]}
        minor=${BASH_REMATCH[2]}
        patch=${BASH_REMATCH[3]}
    else
        echo -e "${RED}Error: Invalid version format in VERSION file${NC}"
        exit 1
    fi
    
    case $bump_type in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            echo -e "${RED}Error: Invalid bump type. Use major, minor, or patch${NC}"
            exit 1
            ;;
    esac
    
    new_version="$major.$minor.$patch"
    echo "$new_version" > "$VERSION_FILE"
    echo -e "${GREEN}Version bumped to $new_version${NC}"
}

create_dev_version() {
    local base_version=$(get_current_version | sed 's/-.*$//')
    local build_number=$(get_build_number)
    local git_hash=$(get_git_hash)
    
    echo "$base_version-dev.$build_number+$git_hash"
}

create_rc_version() {
    local base_version=$(get_current_version | sed 's/-.*$//')
    local rc_number=1
    
    # Check if there are existing RC tags
    if git tag -l "${base_version}-rc*" | grep -q .; then
        rc_number=$(git tag -l "${base_version}-rc*" | sed "s/${base_version}-rc//" | sort -n | tail -1)
        rc_number=$((rc_number + 1))
    fi
    
    echo "$base_version-rc.$rc_number"
}

create_release_version() {
    if [[ "$CURRENT_BRANCH" != "main" ]]; then
        echo -e "${RED}Error: Release creation only allowed on main branch${NC}"
        exit 1
    fi
    
    local base_version=$(get_current_version | sed 's/-.*$//')
    echo "$base_version"
}

create_tag() {
    local version=$(get_current_version)
    
    if git tag -l "v$version" | grep -q .; then
        echo -e "${YELLOW}Warning: Tag v$version already exists${NC}"
        return
    fi
    
    git tag -a "v$version" -m "Release version $version"
    echo -e "${GREEN}Created tag v$version${NC}"
    echo -e "${BLUE}Push tag with: git push origin v$version${NC}"
}

update_frontend_version() {
    local version=$1
    local package_json="$SCRIPT_DIR/frontend/app/package.json"
    
    if [[ -f "$package_json" ]]; then
        # Update package.json version
        sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" "$package_json"
        if [[ "${QUIET:-}" != "true" ]]; then
            echo -e "${GREEN}Updated frontend version to $version${NC}"
        fi
    fi
}

update_backend_version() {
    local version=$1
    local init_file="$SCRIPT_DIR/backend/app/__init__.py"
    
    # Create or update __init__.py with version
    mkdir -p "$(dirname "$init_file")"
    echo "__version__ = \"$version\"" > "$init_file"
    if [[ "${QUIET:-}" != "true" ]]; then
        echo -e "${GREEN}Updated backend version to $version${NC}"
    fi
}

main() {
    case "${1:-}" in
        "current")
            if [[ "${QUIET:-}" == "true" ]]; then
                echo "$(get_current_version)"
            else
                echo "Current version: $(get_current_version)"
                echo "Branch: $CURRENT_BRANCH"
                if [[ "$CURRENT_BRANCH" == "dev" ]]; then
                    echo "Dev version: $(create_dev_version)"
                fi
            fi
            ;;
        "bump")
            if [[ -z "${2:-}" ]]; then
                echo -e "${RED}Error: Bump type required (major|minor|patch)${NC}"
                usage
                exit 1
            fi
            bump_version "$2"
            ;;
        "dev")
            dev_version=$(create_dev_version)
            if [[ "${QUIET:-}" == "true" ]]; then
                echo "$dev_version"
            else
                echo -e "${BLUE}Dev version: $dev_version${NC}"
            fi
            update_frontend_version "$dev_version"
            update_backend_version "$dev_version"
            ;;
        "rc")
            rc_version=$(create_rc_version)
            echo "$rc_version" > "$VERSION_FILE"
            if [[ "${QUIET:-}" == "true" ]]; then
                echo "$rc_version"
            else
                echo -e "${YELLOW}Release candidate: $rc_version${NC}"
            fi
            update_frontend_version "$rc_version"
            update_backend_version "$rc_version"
            ;;
        "release")
            release_version=$(create_release_version)
            echo "$release_version" > "$VERSION_FILE"
            if [[ "${QUIET:-}" == "true" ]]; then
                echo "$release_version"
            else
                echo -e "${GREEN}Release version: $release_version${NC}"
            fi
            update_frontend_version "$release_version"
            update_backend_version "$release_version"
            ;;
        "tag")
            create_tag
            ;;
        "help"|"--help"|"-h")
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown command${NC}"
            usage
            exit 1
            ;;
    esac
}

main "$@"
