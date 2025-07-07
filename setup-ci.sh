#!/bin/bash

# GitHub Actions CI/CD Setup Script
# This script helps set up the development environment for testing CI/CD locally

set -e

echo "🚀 Setting up Kuroibara CI/CD environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    # Check for Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check for Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check for Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    # Check for Snyk (optional)
    if command -v snyk &> /dev/null; then
        print_status "Snyk CLI found ✓"
    else
        print_warning "Snyk CLI not found (optional for local development)"
        print_warning "Snyk scanning will run automatically in GitHub Actions"
    fi
    
    print_status "All requirements are satisfied ✓"
}

# Install backend dependencies
setup_backend() {
    print_status "Setting up backend environment..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing backend dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install black isort flake8 mypy pytest-cov pytest-xdist
    
    print_status "Backend setup complete ✓"
    cd ..
}

# Install frontend dependencies
setup_frontend() {
    print_status "Setting up frontend environment..."
    
    cd frontend/app
    
    # Install dependencies
    print_status "Installing frontend dependencies..."
    npm install
    
    print_status "Frontend setup complete ✓"
    cd ../..
}

# Run tests locally
run_tests() {
    print_status "Running tests locally..."
    
    # Backend tests
    print_status "Running backend tests..."
    cd backend
    source venv/bin/activate
    
    # Create test environment file
    cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test_kuroibara
SECRET_KEY=test-secret-key-for-local-testing
JWT_SECRET_KEY=test-jwt-secret-key-for-local-testing
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=testing
EOF
    
    # Run tests
    pytest -v tests/
    
    # Code quality checks
    print_status "Running code quality checks..."
    black --check .
    isort --check-only .
    flake8 .
    
    cd ..
    
    # Frontend tests
    print_status "Running frontend tests..."
    cd frontend/app
    npm run test:run
    npm run lint
    npm run type-check
    
    cd ../..
    
    print_status "All tests completed ✓"
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build backend image
    print_status "Building backend image..."
    docker build -t kuroibara-backend:local ./backend
    
    # Build frontend image
    print_status "Building frontend image..."
    docker build -t kuroibara-frontend:local ./frontend
    
    print_status "Docker images built successfully ✓"
}

# Main execution
main() {
    echo "======================================"
    echo "🔧 Kuroibara CI/CD Local Setup"
    echo "======================================"
    echo
    
    check_requirements
    
    # Ask user what they want to do
    echo "What would you like to do?"
    echo "1) Setup development environment"
    echo "2) Run tests only"
    echo "3) Build Docker images only"
    echo "4) Full setup (environment + tests + docker)"
    echo "5) Exit"
    echo
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            setup_backend
            setup_frontend
            ;;
        2)
            run_tests
            ;;
        3)
            build_images
            ;;
        4)
            setup_backend
            setup_frontend
            run_tests
            build_images
            ;;
        5)
            print_status "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please run the script again."
            exit 1
            ;;
    esac
    
    echo
    print_status "Setup completed successfully! 🎉"
    echo
    echo "Next steps:"
    echo "- Create a pull request to test the CI/CD pipeline"
    echo "- Check the Actions tab in your GitHub repository"
    echo "- Review the .github/README.md for more information"
    echo
}

# Run main function
main "$@"
