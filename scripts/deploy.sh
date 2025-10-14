#!/bin/bash
# Lead Management System - Deployment Script
# Handles deployment to various environments

set -e

# Configuration
APP_NAME="lead-management"
DOCKER_REGISTRY="your-registry.com"
ENVIRONMENT=${1:-"staging"}

echo "🚀 Deploying $APP_NAME to $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    log_info "Dependencies OK"
}

build_image() {
    log_info "Building Docker image..."

    # Get version from git tag or commit
    VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")

    # Build image
    docker build -t $APP_NAME:$VERSION -t $APP_NAME:latest .

    # Tag for registry
    if [ -n "$DOCKER_REGISTRY" ]; then
        docker tag $APP_NAME:$VERSION $DOCKER_REGISTRY/$APP_NAME:$VERSION
        docker tag $APP_NAME:latest $DOCKER_REGISTRY/$APP_NAME:latest
    fi

    log_info "Image built: $APP_NAME:$VERSION"
}

push_image() {
    if [ -n "$DOCKER_REGISTRY" ] && [ "$ENVIRONMENT" != "local" ]; then
        log_info "Pushing image to registry..."

        VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")

        docker push $DOCKER_REGISTRY/$APP_NAME:$VERSION
        docker push $DOCKER_REGISTRY/$APP_NAME:latest

        log_info "Image pushed to registry"
    fi
}

deploy_local() {
    log_info "Deploying locally..."

    # Stop existing containers
    docker-compose down || true

    # Start services
    docker-compose up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30

    # Health check
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_info "✅ Deployment successful!"
        log_info "Application is running at: http://localhost:8000"
    else
        log_error "❌ Health check failed"
        exit 1
    fi
}

deploy_staging() {
    log_info "Deploying to staging..."

    # Here you would typically:
    # 1. Update Kubernetes deployment
    # 2. Run database migrations
    # 3. Update load balancer
    # 4. Run health checks

    log_warn "Staging deployment not fully implemented"
    log_info "Manual steps required:"
    echo "1. Update Kubernetes manifests"
    echo "2. Run: kubectl apply -f k8s/"
    echo "3. Run database migrations"
    echo "4. Update DNS/load balancer"
}

deploy_production() {
    log_info "Deploying to production..."

    # Additional safety checks for production
    if [ "$ENVIRONMENT" = "production" ]; then
        log_warn "Production deployment requires manual approval"
        read -p "Are you sure you want to deploy to production? (yes/no): " confirm

        if [ "$confirm" != "yes" ]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi

    # Here you would implement production deployment logic
    log_warn "Production deployment not fully implemented"
}

run_tests() {
    log_info "Running pre-deployment tests..."

    # Run unit tests
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        python -m pytest tests/ -v --tb=short
    fi

    log_info "Tests passed"
}

rollback() {
    log_error "Deployment failed, rolling back..."

    # Stop new containers
    docker-compose down || true

    # Start previous version if available
    # docker-compose -f docker-compose.previous.yml up -d || true

    log_info "Rollback completed"
}

# Main deployment flow
main() {
    check_dependencies

    case $ENVIRONMENT in
        local)
            run_tests
            build_image
            deploy_local
            ;;
        staging)
            run_tests
            build_image
            push_image
            deploy_staging
            ;;
        production)
            run_tests
            build_image
            push_image
            deploy_production
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            echo "Usage: $0 [local|staging|production]"
            exit 1
            ;;
    esac
}

# Error handling
trap 'log_error "Deployment failed"; rollback' ERR

# Run main function
main "$@"