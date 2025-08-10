#!/bin/bash

# Pre-deployment checklist script
set -e

echo "🔍 Running pre-deployment checks..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

echo "📋 Checking environment configuration..."

# Check .env file
if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    # Check required variables
    required_vars=("SECRET_KEY" "DB_USER" "DB_PASSWORD" "DB_NAME" "META_APP_ID" "META_APP_SECRET")
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env && ! grep -q "^${var}=$" .env; then
            check_pass "$var is set"
        else
            check_fail "$var is missing or empty in .env"
        fi
    done
    
    # Check for default values that should be changed
    if grep -q "your-super-secure-secret-key-here" .env; then
        check_fail "SECRET_KEY still has default value"
    fi
    
    if grep -q "secure_password_here" .env; then
        check_fail "DB_PASSWORD still has default value"
    fi
    
else
    check_fail ".env file not found. Copy .env.example to .env and configure it."
fi

echo ""
echo "🐍 Checking Python environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    check_pass "Python version $python_version is compatible"
else
    check_fail "Python 3.8+ required. Found: $python_version"
fi

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"
else
    check_fail "requirements.txt not found"
fi

echo ""
echo "🗄️  Checking database connectivity..."

# Check if MySQL is running
if command -v mysql >/dev/null 2>&1; then
    if systemctl is-active --quiet mysql 2>/dev/null || service mysql status >/dev/null 2>&1; then
        check_pass "MySQL service is running"
        
        # Test database connection if .env exists
        if [ -f ".env" ]; then
            source .env
            if mysql -u"$DB_USER" -p"$DB_PASSWORD" -h"${DB_HOST:-localhost}" -e "USE $DB_NAME;" 2>/dev/null; then
                check_pass "Database connection successful"
            else
                check_fail "Cannot connect to database. Check credentials and database exists."
            fi
        fi
    else
        check_fail "MySQL service is not running"
    fi
else
    check_fail "MySQL client not installed"
fi

echo ""
echo "🌐 Checking system requirements..."

# Check if nginx is installed
if command -v nginx >/dev/null 2>&1; then
    check_pass "Nginx is installed"
else
    check_warn "Nginx not installed (will be installed during deployment)"
fi

# Check if systemctl is available
if command -v systemctl >/dev/null 2>&1; then
    check_pass "systemd is available"
else
    check_fail "systemd not available (required for service management)"
fi

# Check disk space
available_space=$(df . | tail -1 | awk '{print $4}')
if [ "$available_space" -gt 1048576 ]; then  # 1GB in KB
    check_pass "Sufficient disk space available"
else
    check_warn "Low disk space. Consider freeing up space."
fi

# Check memory
total_memory=$(free -m | awk 'NR==2{print $2}')
if [ "$total_memory" -gt 1024 ]; then  # 1GB
    check_pass "Sufficient memory available ($total_memory MB)"
else
    check_warn "Low memory ($total_memory MB). Consider upgrading for better performance."
fi

echo ""
echo "🔒 Checking security configuration..."

# Check file permissions
if [ -f ".env" ]; then
    env_perms=$(stat -c "%a" .env)
    if [ "$env_perms" = "600" ] || [ "$env_perms" = "644" ]; then
        check_pass ".env file permissions are secure"
    else
        check_warn ".env file permissions should be 600 or 644"
    fi
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    check_warn "Running as root. Consider using a non-root user for deployment."
fi

echo ""
echo "📊 Pre-deployment check summary:"
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical checks passed! Ready for deployment.${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Please review warnings above.${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ $ERRORS critical issues found. Please fix before deploying.${NC}"
    exit 1
fi