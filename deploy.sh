#!/bin/bash

# WhatsApp Business Platform Deployment Script for Low Memory Systems

echo "Starting deployment on low-memory system..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create instance directory if it doesn't exist
mkdir -p instance

# Initialize database if it doesn't exist
if [ ! -f "instance/whatsapp_business.db" ]; then
    echo "Initializing database..."
    python3 -c "
from app import create_app
from app.models import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"
fi

# Run with Gunicorn for better memory management
echo "Starting application with Gunicorn..."
gunicorn --bind 0.0.0.0:5001 --workers 1 --threads 2 --worker-class gthread --max-requests 1000 --max-requests-jitter 100 --preload --timeout 30 run:app