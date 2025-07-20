from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    onboarding_status = db.Column(db.Enum('Pending', 'In Progress', 'Verified'), default='Pending')
    waba_id = db.Column(db.String(64))
    phone_number_id = db.Column(db.String(64))
    whatsapp_access_token = db.Column(db.Text)
    uploads = db.relationship('Upload', backref='user', lazy=True)


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
    category = db.Column(db.Enum('TRANSACTIONAL', 'MARKETING', 'OTP'), default='TRANSACTIONAL')
    header_type = db.Column(db.Enum('NONE', 'TEXT', 'IMAGE'), default='NONE')
    header_text = db.Column(db.String(255))
    header_image_url = db.Column(db.String(255))
    footer_text = db.Column(db.String(255))
    buttons_json = db.Column(db.Text)


class MessageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient = db.Column(db.String(32), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    meta_message_id = db.Column(db.String(128))
    status = db.Column(db.String(32), default='sent')  # sent, delivered, read, failed, etc.
    created_at = db.Column(db.DateTime, server_default=db.func.now())
