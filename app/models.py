from app import db
from flask_login import UserMixin

class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    message_limit = db.Column(db.Integer, nullable=False)
    features = db.Column(db.Text)  # JSON string of features
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')
    status = db.Column(db.Enum('pending', 'completed', 'failed', 'refunded'), default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    user = db.relationship('User', backref='payments')
    plan = db.relationship('SubscriptionPlan', backref='payments')


class UserSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'))
    status = db.Column(db.Enum('active', 'cancelled', 'expired'), default='active')
    start_date = db.Column(db.DateTime, server_default=db.func.now())
    end_date = db.Column(db.DateTime, nullable=False)
    auto_renew = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    plan = db.relationship('SubscriptionPlan', backref='subscriptions')
    payment = db.relationship('Payment', backref='subscription')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    business_name = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    onboarding_status = db.Column(db.Enum('Pending', 'In Progress', 'Verified'), default='Pending')
    waba_id = db.Column(db.String(64))
    phone_number_id = db.Column(db.String(64))
    whatsapp_access_token = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)  # Document verification status
    message_limit = db.Column(db.Integer, default=100)  # Monthly message limit (reduced for free tier)
    messages_sent_this_month = db.Column(db.Integer, default=0)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscription.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    uploads = db.relationship('Upload', backref='user', lazy=True)
    subscription = db.relationship('UserSubscription', backref='user', foreign_keys=[subscription_id])
    
    def can_send_message(self):
        """Check if user can send more messages this month"""
        return self.messages_sent_this_month < self.message_limit
    
    def get_remaining_messages(self):
        """Get remaining messages for this month"""
        return max(0, self.message_limit - self.messages_sent_this_month)
    
    def get_current_plan(self):
        """Get user's current subscription plan"""
        if self.subscription and self.subscription.status == 'active':
            from datetime import datetime
            if self.subscription.end_date > datetime.now():
                return self.subscription.plan
        return None
    
    def is_premium(self):
        """Check if user has an active premium subscription"""
        plan = self.get_current_plan()
        return plan is not None and plan.name != 'Free'


class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filetype = db.Column(db.String(20))  # 'PAN' or 'GST'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('Pending', 'Approved', 'Rejected'), default='Pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    meta_template_id = db.Column(db.String(100))  # Meta's template ID
    category = db.Column(db.Enum('TRANSACTIONAL', 'MARKETING', 'OTP', 'UTILITY'), default='TRANSACTIONAL')
    header_type = db.Column(db.Enum('NONE', 'TEXT', 'IMAGE'), default='NONE')
    header_text = db.Column(db.String(255))
    header_image_url = db.Column(db.String(255))
    footer_text = db.Column(db.String(255))
    buttons_json = db.Column(db.Text)





class ScheduledMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient = db.Column(db.String(32), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum('pending', 'sent', 'failed', 'cancelled'), default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone_number = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150))
    last_message_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relationships
    user = db.relationship('User', backref='contacts')
    
    def get_last_message(self):
        """Get the last message sent to this contact"""
        return MessageHistory.query.filter_by(
            user_id=self.user_id, 
            recipient=self.phone_number
        ).order_by(MessageHistory.created_at.desc()).first()
    
    def get_message_count(self):
        """Get total messages sent to this contact"""
        return MessageHistory.query.filter_by(
            user_id=self.user_id, 
            recipient=self.phone_number
        ).count()


class MessageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient = db.Column(db.String(32), nullable=False)
    recipient_name = db.Column(db.String(100))  # Optional contact name
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    message_content = db.Column(db.Text)  # Store the actual message content sent
    message_type = db.Column(db.Enum('template', 'text', 'media'), default='template')
    meta_message_id = db.Column(db.String(128))
    status = db.Column(db.String(32), default='sent')  # sent, delivered, read, failed, etc.
    scheduled_message_id = db.Column(db.Integer, db.ForeignKey('scheduled_message.id'))  # Link to scheduled message if applicable
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relationships
    template = db.relationship('Template', backref='messages')
    user = db.relationship('User', backref='sent_messages')
    
    def get_contact(self):
        """Get or create contact for this message"""
        contact = Contact.query.filter_by(
            user_id=self.user_id, 
            phone_number=self.recipient
        ).first()
        
        if not contact:
            contact = Contact(
                user_id=self.user_id,
                phone_number=self.recipient,
                name=self.recipient_name,
                last_message_at=self.created_at
            )
            db.session.add(contact)
            db.session.commit()
        else:
            # Update last message time
            contact.last_message_at = self.created_at
            if self.recipient_name and not contact.name:
                contact.name = self.recipient_name
            db.session.commit()
        
        return contact
