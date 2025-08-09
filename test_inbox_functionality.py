#!/usr/bin/env python3
"""
Test script to verify inbox functionality
Run this after completing the database migration
"""

from app import create_app, db
from app.models import User, Contact, MessageHistory, Template

def test_inbox_functionality():
    """Test the inbox functionality"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Inbox Functionality...")
        print("=" * 50)
        
        # Test 1: Check if Contact table exists
        try:
            contact_count = Contact.query.count()
            print(f"✅ Contact table exists with {contact_count} contacts")
        except Exception as e:
            print(f"❌ Contact table error: {e}")
            return False
        
        # Test 2: Check MessageHistory updates
        try:
            messages_with_content = MessageHistory.query.filter(
                MessageHistory.message_content.isnot(None)
            ).count()
            total_messages = MessageHistory.query.count()
            print(f"✅ MessageHistory updated: {messages_with_content}/{total_messages} messages have content")
        except Exception as e:
            print(f"❌ MessageHistory error: {e}")
            return False
        
        # Test 3: Check relationships
        try:
            # Get a user with messages
            user_with_messages = db.session.query(User).join(MessageHistory).first()
            if user_with_messages:
                user_contacts = Contact.query.filter_by(user_id=user_with_messages.id).count()
                user_messages = MessageHistory.query.filter_by(user_id=user_with_messages.id).count()
                print(f"✅ User {user_with_messages.email} has {user_contacts} contacts and {user_messages} messages")
            else:
                print("ℹ️ No users with messages found (this is normal for new installations)")
        except Exception as e:
            print(f"❌ Relationship error: {e}")
            return False
        
        # Test 4: Test Contact methods
        try:
            contact = Contact.query.first()
            if contact:
                last_message = contact.get_last_message()
                message_count = contact.get_message_count()
                print(f"✅ Contact methods work: {contact.phone_number} has {message_count} messages")
            else:
                print("ℹ️ No contacts found (this is normal for new installations)")
        except Exception as e:
            print(f"❌ Contact methods error: {e}")
            return False
        
        print("=" * 50)
        print("✅ All inbox functionality tests passed!")
        return True

if __name__ == "__main__":
    test_inbox_functionality()