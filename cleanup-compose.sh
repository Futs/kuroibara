#!/bin/bash

# Kuroibara Docker Cleanup Script
# This script removes all Kuroibara-related Docker images, volumes, containers, and networks

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

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to stop and remove containers
cleanup_containers() {
    print_status "Stopping and removing Kuroibara containers..."
    
    # Stop containers using both compose files
    if [ -f "docker-compose.yml" ]; then
        print_status "Stopping production containers..."
        docker compose -f docker-compose.yml down --remove-orphans 2>/dev/null || true
    fi
    
    if [ -f "docker-compose.dev.yml" ]; then
        print_status "Stopping development containers..."
        docker compose -f docker-compose.dev.yml down --remove-orphans 2>/dev/null || true
    fi
    
    # Remove any remaining Kuroibara containers
    local containers=$(docker ps -a --filter "name=kuroibara" --format "{{.ID}}" 2>/dev/null || true)
    if [ -n "$containers" ]; then
        print_status "Removing remaining Kuroibara containers..."
        echo "$containers" | xargs docker rm -f 2>/dev/null || true
    fi
    
    print_success "Containers cleanup completed"
}

# Function to remove images
cleanup_images() {
    print_status "Removing Kuroibara Docker images..."
    
    # List of Kuroibara-related images
    local images=(
        "futs/kuroibara-backend"
        "futs/kuroibara-frontend"
        "kuroibara-backend"
        "kuroibara-frontend"
        "kuroibara_backend"
        "kuroibara_frontend"
    )
    
    for image in "${images[@]}"; do
        # Remove all tags of the image
        local image_ids=$(docker images --filter "reference=${image}" --format "{{.ID}}" 2>/dev/null || true)
        if [ -n "$image_ids" ]; then
            print_status "Removing image: $image"
            echo "$image_ids" | xargs docker rmi -f 2>/dev/null || true
        fi
    done
    
    # Remove dangling images related to Kuroibara
    local dangling=$(docker images -f "dangling=true" --format "{{.ID}}" 2>/dev/null || true)
    if [ -n "$dangling" ]; then
        print_status "Removing dangling images..."
        echo "$dangling" | xargs docker rmi -f 2>/dev/null || true
    fi
    
    print_success "Images cleanup completed"
}

# Function to remove volumes
cleanup_volumes() {
    print_status "Removing Kuroibara Docker volumes..."
    
    # List of Kuroibara-related volumes
    local volumes=(
        "kuroibara_postgres_data"
        "kuroibara_valkey_data"
        "kuroibara_manga_storage"
        "postgres_data"
        "valkey_data"
        "manga_storage"
    )
    
    for volume in "${volumes[@]}"; do
        if docker volume inspect "$volume" >/dev/null 2>&1; then
            print_status "Removing volume: $volume"
            docker volume rm "$volume" 2>/dev/null || true
        fi
    done
    
    # Remove any volumes with kuroibara in the name
    local kuroibara_volumes=$(docker volume ls --filter "name=kuroibara" --format "{{.Name}}" 2>/dev/null || true)
    if [ -n "$kuroibara_volumes" ]; then
        print_status "Removing additional Kuroibara volumes..."
        echo "$kuroibara_volumes" | xargs docker volume rm 2>/dev/null || true
    fi
    
    print_success "Volumes cleanup completed"
}

# Function to remove networks
cleanup_networks() {
    print_status "Removing Kuroibara Docker networks..."
    
    # List of Kuroibara-related networks
    local networks=(
        "kuroibara-network"
        "kuroibara_kuroibara-network"
        "kuroibara_default"
    )
    
    for network in "${networks[@]}"; do
        if docker network inspect "$network" >/dev/null 2>&1; then
            print_status "Removing network: $network"
            docker network rm "$network" 2>/dev/null || true
        fi
    done
    
    print_success "Networks cleanup completed"
}

# Function to clean up build cache
cleanup_build_cache() {
    print_status "Cleaning up Docker build cache..."
    docker builder prune -f >/dev/null 2>&1 || true
    print_success "Build cache cleanup completed"
}

# Function to show disk space freed
show_disk_usage() {
    print_status "Docker system disk usage after cleanup:"
    docker system df 2>/dev/null || true
}

# Main cleanup function
main() {
    echo "=================================================="
    echo "    Kuroibara Docker Cleanup Script"
    echo "=================================================="
    echo
    
    # Check if Docker is running
    check_docker
    
    # Ask for confirmation
    echo -e "${YELLOW}This will remove ALL Kuroibara-related Docker resources:${NC}"
    echo "  - Containers (running and stopped)"
    echo "  - Images (all tags)"
    echo "  - Volumes (including data)"
    echo "  - Networks"
    echo "  - Build cache"
    echo
    echo -e "${RED}WARNING: This will permanently delete all Kuroibara data!${NC}"
    echo
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Cleanup cancelled by user"
        exit 0
    fi
    
    echo
    print_status "Starting cleanup process..."
    echo
    
    # Perform cleanup steps
    cleanup_containers
    echo
    cleanup_images
    echo
    cleanup_volumes
    echo
    cleanup_networks
    echo
    cleanup_build_cache
    echo
    
    # Show final status
    show_disk_usage
    echo
    print_success "Kuroibara cleanup completed successfully!"
    echo
    print_status "To rebuild Kuroibara, run:"
    echo "  Production: docker compose up -d"
    echo "  Development: docker compose -f docker-compose.dev.yml up -d"
}

# Run main function
main "$@"
