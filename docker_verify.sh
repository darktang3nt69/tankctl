#!/bin/bash

# Docker Build & Deployment Verification Script for TankCtl
# This script validates the Docker setup before deployment

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# Functions for output
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
}

print_check() {
    echo -n "  ✓ $1... "
}

print_pass() {
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}FAIL${NC}"
    echo -e "    ${RED}→ $1${NC}"
    ((FAILED++))
}

print_warn() {
    echo -e "${YELLOW}WARN${NC}"
    echo -e "    ${YELLOW}→ $1${NC}"
    ((WARNINGS++))
}

# Pre-flight checks
print_header "PRE-FLIGHT CHECKS"

# Check Docker
print_check "Docker installed"
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "${GREEN}PASS${NC} ($docker_version)"
    ((PASSED++))
else
    print_fail "Docker not found. Install from https://docs.docker.com/install/"
fi

# Check Docker Compose
print_check "Docker Compose installed"
if command -v docker-compose &> /dev/null; then
    compose_version=$(docker-compose --version)
    echo -e "${GREEN}PASS${NC} ($compose_version)"
    ((PASSED++))
else
    print_fail "Docker Compose not found. Install from https://docs.docker.com/compose/install/"
fi

# Check Docker daemon running
print_check "Docker daemon running"
if docker ps &> /dev/null; then
    print_pass
else
    print_fail "Docker daemon not running. Try 'sudo systemctl start docker' or 'docker ps' for more info"
fi

# Check disk space
print_check "Disk space available"
available=$(df / | awk 'NR==2 {print $4}')
if [ "$available" -gt 4194304 ]; then  # 4GB in KB
    echo -e "${GREEN}PASS${NC} ($(numfmt --to=iec $((available * 1024))) available)"
    ((PASSED++))
else
    print_warn "Low disk space (only $(numfmt --to=iec $((available * 1024))) available). May fail during build."
fi

# File checks
print_header "FILE STRUCTURE CHECKS"

# Check Dockerfile
print_check "Dockerfile exists"
if [ -f "Dockerfile" ]; then
    print_pass
else
    print_fail "Dockerfile not found in current directory"
fi

# Check .dockerignore
print_check ".dockerignore exists"
if [ -f ".dockerignore" ]; then
    print_pass
else
    print_fail ".dockerignore not found. Docker build context may be too large."
fi

# Check requirements.txt
print_check "requirements.txt exists"
if [ -f "requirements.txt" ]; then
    print_pass
else
    print_fail "requirements.txt not found"
fi

# Check docker-compose.yml
print_check "docker-compose.yml exists"
if [ -f "docker-compose.yml" ]; then
    print_pass
else
    print_fail "docker-compose.yml not found"
fi

# Check src/api/main.py
print_check "src/api/main.py exists"
if [ -f "src/api/main.py" ]; then
    print_pass
else
    print_fail "src/api/main.py not found. Backend code missing."
fi

# Dockerfile validation
print_header "DOCKERFILE VALIDATION"

# Check multi-stage build
print_check "Dockerfile has multi-stage build"
stage_count=$(grep -c "^FROM" Dockerfile 2>/dev/null || echo 0)
if [ "$stage_count" -eq 2 ]; then
    print_pass
else
    print_fail "Expected 2 FROM statements, found $stage_count. Multi-stage build may not be configured."
fi

# Check Python version
print_check "Dockerfile uses Python 3.11"
if grep -q "python:3.11" Dockerfile; then
    print_pass
else
    print_warn "Not using python:3.11. Check if intentional."
fi

# Check non-root user
print_check "Dockerfile creates non-root user"
if grep -q "useradd.*tankctl" Dockerfile; then
    print_pass
else
    print_warn "No non-root user found. Security may be compromised."
fi

# Check health check
print_check "Dockerfile has HEALTHCHECK"
if grep -q "^HEALTHCHECK" Dockerfile; then
    print_pass
else
    print_warn "No HEALTHCHECK found. Container health may not be monitored properly."
fi

# Requirements validation
print_header "REQUIREMENTS VALIDATION"

# Check essential packages
packages=("fastapi" "uvicorn" "sqlalchemy" "paho-mqtt" "python-dotenv")
for pkg in "${packages[@]}"; do
    print_check "requirements.txt includes $pkg"
    if grep -q "^$pkg" requirements.txt; then
        print_pass
    else
        print_fail "Package '$pkg' not found in requirements.txt"
    fi
done

# Docker-compose validation
print_header "DOCKER-COMPOSE VALIDATION"

# Check services
services=("backend" "postgres" "mosquitto" "timescaledb")
for svc in "${services[@]}"; do
    print_check "docker-compose.yml includes $svc service"
    if grep -q "^  $svc:" docker-compose.yml; then
        print_pass
    else
        print_fail "Service '$svc' not found in docker-compose.yml"
    fi
done

# Check health checks on services
print_check "Services have health checks"
if grep -c "healthcheck:" docker-compose.yml | grep -q "[3-9]"; then
    print_pass
else
    print_warn "Not all services have health checks configured"
fi

# Build test
print_header "BUILD TEST"

print_check "Building Docker image"
if docker build -q -t tankctl-backend:test . &> /tmp/docker_build.log; then
    print_pass
    
    # Check image size
    print_check "Final image size"
    size=$(docker images --no-trunc --quiet tankctl-backend:test | xargs docker inspect --format='{{.Size}}' | awk '{print int($1/1024/1024)}')
    if [ "$size" -lt 300 ]; then
        echo -e "${GREEN}PASS${NC} (${size}MB)"
        ((PASSED++))
    else
        print_warn "Image size is ${size}MB. Target is <200MB. Check .dockerignore and remove unnecessary files."
    fi
else
    print_fail "Docker build failed. See details below:\n$(head -20 /tmp/docker_build.log)"
fi

# Runtime test
print_header "RUNTIME TEST"

# Test image can start
print_check "Docker image starts successfully"
if docker run --rm -d --name tankctl-test tankctl-backend:test &> /dev/null; then
    sleep 2
    if docker ps | grep -q tankctl-test; then
        docker stop tankctl-test 2>/dev/null || true
        print_pass
    else
        print_fail "Container exited immediately"
    fi
else
    print_fail "Failed to start container"
fi

# Docker Compose test
print_header "DOCKER-COMPOSE TESTS"

print_check "docker-compose.yml is valid YAML"
if docker-compose config > /dev/null 2>&1; then
    print_pass
else
    print_fail "docker-compose.yml has syntax errors"
fi

# Cleanup
print_header "CLEANUP"

print_check "Removing test image"
docker rmi tankctl-backend:test 2>/dev/null || true
print_pass

# Summary
print_header "TEST SUMMARY"

total=$((PASSED + FAILED + WARNINGS))
echo -e "  ${GREEN}✓ Passed:  $PASSED${NC}"
echo -e "  ${RED}✗ Failed:  $FAILED${NC}"
echo -e "  ${YELLOW}⚠ Warnings: $WARNINGS${NC}"
echo -e "  Total:  $total"

echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}All checks passed! Ready for deployment.${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Build production image:"
    echo "     docker build -t tankctl-backend:latest ."
    echo "  2. Start all services:"
    echo "     docker-compose up -d"
    echo "  3. Verify health:"
    echo "     curl http://localhost:8000/health"
    echo ""
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════${NC}"
    echo -e "${RED}$FAILED check(s) failed. Fix issues above.${NC}"
    echo -e "${RED}═══════════════════════════════════════${NC}"
    echo ""
    exit 1
fi
