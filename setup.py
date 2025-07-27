#!/usr/bin/env python3
"""
Setup script for WhatsApp Business API Onboarding Portal
"""

import os
import sys
from subprocess import run, PIPE

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    result = run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ {description} completed successfully")
    return True

def main():
    print("🚀 Setting up WhatsApp Business API Onboarding Portal")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Create uploads directory
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"✅ Created {uploads_dir} directory")
    
    # Initialize database
    print("🔄 Initializing database...")
    try:
        from app import create_app, db
        app = create_app()
        with app.app_context():
            db.create_all()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("⚠️  Please make sure MySQL is running and configured in config.py")
    
    # Check if Node.js is installed
    node_check = run("node --version", shell=True, capture_output=True, text=True)
    if node_check.returncode != 0:
        print("⚠️  Node.js not found. Please install Node.js 16+ to run the React frontend")
    else:
        print(f"✅ Node.js found: {node_check.stdout.strip()}")
        
        # Install frontend dependencies
        if os.path.exists("frontend"):
            os.chdir("frontend")
            if not run_command("npm install", "Installing React dependencies"):
                print("❌ Failed to install React dependencies")
            else:
                print("✅ Frontend setup completed")
            os.chdir("..")
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Update config.py with your Meta App credentials")
    print("2. Start the Flask backend: python run.py")
    print("3. Start the React frontend: cd frontend && npm start")
    print("4. Access the application at http://localhost:3000")

if __name__ == "__main__":
    main()