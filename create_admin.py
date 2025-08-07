#!/usr/bin/env python3
"""
Script to create an admin user for testing
"""

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        admin_email = "admin@test.com"
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if existing_admin:
            print(f"Admin user {admin_email} already exists. Updating password...")
            existing_admin.password = generate_password_hash("Test@123")
            db.session.commit()
            print("✅ Admin password updated successfully!")
        else:
            # Create new admin user
            admin_user = User(
                email=admin_email,
                password=generate_password_hash("Test@123"),
                business_name="Test Admin",
                phone_number="1234567890",
                onboarding_status="Verified",
                is_verified=True,
                message_limit=10000
            )
            
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully!")
        
        print(f"Login credentials:")
        print(f"Email: {admin_email}")
        print(f"Password: Test@123")

if __name__ == '__main__':
    create_admin_user()