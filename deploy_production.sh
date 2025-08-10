#!/bin/bash

# Production Deployment Script for WhatsApp Business Platform
set -e

echo "🚀 Starting production deployment..."

# Configuration
APP_NAME="whatsapp-business"
APP_USER="www-data"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="$APP_NAME"
NGINX_SITE="$APP_NAME"

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

print_status "Checking system requirements..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8+ required. Found: $python_version"
    exit 1
fi

# Check if MySQL is running
if ! systemctl is-active --quiet mysql; then
    print_error "MySQL is not running. Please start MySQL service."
    exit 1
fi

print_status "Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev mysql-client nginx supervisor

print_status "Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
print_status "Copying application files..."
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='.git' --exclude='instance' . $APP_DIR/

# Create virtual environment
print_status "Creating virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create necessary directories
print_status "Creating application directories..."
sudo mkdir -p /var/log/$APP_NAME
sudo mkdir -p $APP_DIR/instance
sudo mkdir -p $APP_DIR/uploads
sudo chown -R $APP_USER:$APP_USER /var/log/$APP_NAME
sudo chown -R $APP_USER:$APP_USER $APP_DIR

# Copy environment file
cp .env $APP_DIR/.env
sudo chown $APP_USER:$APP_USER $APP_DIR/.env
sudo chmod 600 $APP_DIR/.env

print_status "Setting up database..."
# Source environment variables
set -a
source $APP_DIR/.env
set +a

# Create database and user if they don't exist
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# Run database migrations
print_status "Running database migrations..."
cd $APP_DIR
source venv/bin/activate
python3 -c "
import os
os.environ['FLASK_ENV'] = 'production'
from app import create_app
from app.models import db
app = create_app('production_config.ProductionConfig')
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"

print_status "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=WhatsApp Business Platform
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=FLASK_ENV=production
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --bind unix:$APP_DIR/$APP_NAME.sock --workers 3 --threads 2 --worker-class gthread --max-requests 1000 --max-requests-jitter 100 --preload --timeout 30 --access-logfile /var/log/$APP_NAME/access.log --error-logfile /var/log/$APP_NAME/error.log run:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/$NGINX_SITE > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration (update paths after obtaining certificates)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # File upload size
    client_max_body_size 16M;
    
    location / {
        proxy_pass http://unix:$APP_DIR/$APP_NAME.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering off;
    }
    
    location /static {
        alias $APP_DIR/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /uploads {
        alias $APP_DIR/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/$APP_NAME > /dev/null << EOF
/var/log/$APP_NAME/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

print_status "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Test Nginx configuration
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    print_status "Nginx configuration is valid and reloaded"
else
    print_error "Nginx configuration test failed"
    exit 1
fi

print_status "Deployment completed successfully!"
print_warning "Next steps:"
echo "1. Update your domain name in /etc/nginx/sites-available/$NGINX_SITE"
echo "2. Obtain SSL certificate: sudo certbot --nginx -d your-domain.com"
echo "3. Update META_REDIRECT_URI in .env to use your domain"
echo "4. Test the application: curl -I http://your-domain.com"
echo "5. Monitor logs: sudo journalctl -u $SERVICE_NAME -f"

print_status "Service status:"
sudo systemctl status $SERVICE_NAME --no-pager -l