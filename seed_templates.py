#!/usr/bin/env python3
"""
Script to populate the template library with common business templates
Run this after creating the database tables
"""

from app import create_app, db
from app.models import TemplateLibrary

def seed_template_library():
    app = create_app()
    
    with app.app_context():
        # Clear existing templates
        TemplateLibrary.query.delete()
        
        templates = [
            # Restaurant Templates
            {
                'name': 'Order Confirmation',
                'category': 'restaurant',
                'content': 'Hi {{customer_name}}, your order #{{order_id}} has been confirmed! Total: ₹{{amount}}. Estimated delivery: {{delivery_time}}. Thank you for choosing {{business_name}}!',
                'description': 'Confirm customer orders with details',
                'header_type': 'TEXT',
                'header_text': '🍽️ Order Confirmed',
                'footer_text': 'Track your order anytime'
            },
            {
                'name': 'Order Ready for Pickup',
                'category': 'restaurant',
                'content': 'Great news! Your order #{{order_id}} is ready for pickup at {{business_name}}. Please collect within 15 minutes to ensure freshness.',
                'description': 'Notify when order is ready',
                'header_type': 'TEXT',
                'header_text': '✅ Order Ready!',
                'footer_text': 'Thank you for your business'
            },
            {
                'name': 'Delivery Update',
                'category': 'restaurant',
                'content': 'Your order #{{order_id}} is out for delivery! Our delivery partner will reach you in {{eta}} minutes. Please keep your phone handy.',
                'description': 'Update customers on delivery status',
                'header_type': 'TEXT',
                'header_text': '🚚 On the Way',
                'footer_text': 'Rate your experience'
            },
            
            # Salon/Beauty Templates
            {
                'name': 'Appointment Confirmation',
                'category': 'salon',
                'content': 'Hi {{customer_name}}, your appointment at {{business_name}} is confirmed for {{date}} at {{time}}. Service: {{service}}. See you soon!',
                'description': 'Confirm beauty appointments',
                'header_type': 'TEXT',
                'header_text': '💄 Appointment Confirmed',
                'footer_text': 'Call us to reschedule'
            },
            {
                'name': 'Appointment Reminder',
                'category': 'salon',
                'content': 'Reminder: You have an appointment tomorrow at {{time}} for {{service}} at {{business_name}}. Please arrive 10 minutes early.',
                'description': 'Remind customers of upcoming appointments',
                'header_type': 'TEXT',
                'header_text': '⏰ Appointment Tomorrow',
                'footer_text': 'Reply CANCEL to reschedule'
            },
            {
                'name': 'Special Offer',
                'category': 'salon',
                'content': '✨ Special offer for you! Get {{discount}}% off on {{service}} this week at {{business_name}}. Book now: {{phone}}',
                'description': 'Promote special offers and discounts',
                'header_type': 'TEXT',
                'header_text': '🎉 Limited Time Offer',
                'footer_text': 'Valid till {{expiry_date}}'
            },
            
            # Retail/Shop Templates
            {
                'name': 'Order Shipped',
                'category': 'retail',
                'content': 'Your order #{{order_id}} has been shipped! Tracking ID: {{tracking_id}}. Expected delivery: {{delivery_date}}. Track: {{tracking_link}}',
                'description': 'Notify customers when orders are shipped',
                'header_type': 'TEXT',
                'header_text': '📦 Order Shipped',
                'footer_text': 'Questions? Contact support'
            },
            {
                'name': 'Payment Reminder',
                'category': 'retail',
                'content': 'Hi {{customer_name}}, this is a friendly reminder that payment of ₹{{amount}} for invoice #{{invoice_id}} is due on {{due_date}}.',
                'description': 'Send payment reminders to customers',
                'header_type': 'TEXT',
                'header_text': '💳 Payment Reminder',
                'footer_text': 'Pay online or visit store'
            },
            {
                'name': 'New Arrival Alert',
                'category': 'retail',
                'content': '🆕 New arrivals at {{business_name}}! Check out our latest {{category}} collection. Visit us or shop online: {{website}}',
                'description': 'Announce new product arrivals',
                'header_type': 'TEXT',
                'header_text': '🛍️ New Collection',
                'footer_text': 'Free delivery on orders above ₹500'
            },
            
            # Service Business Templates
            {
                'name': 'Service Completion',
                'category': 'service',
                'content': 'Thank you {{customer_name}}! Your {{service_type}} service has been completed. Total: ₹{{amount}}. We hope you\'re satisfied with our work!',
                'description': 'Confirm service completion',
                'header_type': 'TEXT',
                'header_text': '✅ Service Completed',
                'footer_text': 'Rate us on Google'
            },
            {
                'name': 'Service Reminder',
                'category': 'service',
                'content': 'Hi {{customer_name}}, it\'s time for your regular {{service_type}} service. Book your appointment with {{business_name}}: {{phone}}',
                'description': 'Remind customers of recurring services',
                'header_type': 'TEXT',
                'header_text': '🔧 Service Due',
                'footer_text': 'Book now for best rates'
            },
            
            # General Business Templates
            {
                'name': 'Welcome Message',
                'category': 'general',
                'content': 'Welcome to {{business_name}}! Thank you for choosing us. We\'re committed to providing you the best service. Contact us anytime: {{phone}}',
                'description': 'Welcome new customers',
                'header_type': 'TEXT',
                'header_text': '👋 Welcome!',
                'footer_text': 'Follow us on social media'
            },
            {
                'name': 'Thank You Message',
                'category': 'general',
                'content': 'Thank you for your business, {{customer_name}}! Your support means everything to us at {{business_name}}. We look forward to serving you again.',
                'description': 'Thank customers after purchase',
                'header_type': 'TEXT',
                'header_text': '🙏 Thank You',
                'footer_text': 'Refer friends and earn rewards'
            },
            {
                'name': 'Holiday Greetings',
                'category': 'general',
                'content': '🎉 {{business_name}} wishes you and your family a very happy {{festival_name}}! May this festival bring joy and prosperity to your life.',
                'description': 'Send festival and holiday wishes',
                'header_type': 'TEXT',
                'header_text': '🎊 Festival Wishes',
                'footer_text': 'Special offers inside!'
            }
        ]
        
        for template_data in templates:
            template = TemplateLibrary(**template_data)
            db.session.add(template)
        
        db.session.commit()
        print(f"✅ Successfully added {len(templates)} templates to the library!")
        
        # Print summary
        categories = db.session.query(TemplateLibrary.category).distinct().all()
        for category in categories:
            count = TemplateLibrary.query.filter_by(category=category[0]).count()
            print(f"   - {category[0].title()}: {count} templates")

if __name__ == '__main__':
    seed_template_library()