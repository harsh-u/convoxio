#!/usr/bin/env python3
"""
Script to populate the subscription plans
Run this after creating the database tables
"""

from app import create_app, db
from app.models import SubscriptionPlan
import json

def seed_subscription_plans():
    app = create_app()
    
    with app.app_context():
        # Clear existing plans
        SubscriptionPlan.query.delete()
        
        plans = [
            {
                'name': 'Starter',
                'price': 0.0,
                'message_limit': 100,
                'features': json.dumps([
                    'Basic message templates',
                    'WhatsApp Business API access',
                    'Message delivery tracking',
                    'Email support'
                ]),
                'is_active': True
            },
            {
                'name': 'Business',
                'price': 999.0,
                'message_limit': 5000,
                'features': json.dumps([
                    'All Starter features',
                    'Bulk messaging (CSV upload)',
                    'Message scheduling',
                    'Advanced analytics',
                    'Priority support',
                    'Custom templates',
                    'Template library access'
                ]),
                'is_active': True
            },
            {
                'name': 'Enterprise',
                'price': 2999.0,
                'message_limit': 25000,
                'features': json.dumps([
                    'All Business features',
                    'API access for integrations',
                    'White-label solution',
                    'Dedicated account manager',
                    '24/7 phone support',
                    'Custom integrations',
                    'Advanced reporting',
                    'Priority template approval'
                ]),
                'is_active': True
            }
        ]
        
        for plan_data in plans:
            plan = SubscriptionPlan(**plan_data)
            db.session.add(plan)
        
        db.session.commit()
        print(f"✅ Successfully added {len(plans)} subscription plans!")
        
        # Print summary
        for plan in SubscriptionPlan.query.all():
            print(f"   - {plan.name}: ₹{plan.price}/month - {plan.message_limit} messages")

if __name__ == '__main__':
    seed_subscription_plans()