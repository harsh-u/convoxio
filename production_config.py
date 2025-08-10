import os
import logging
from datetime import timedelta

class ProductionConfig:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    WTF_CSRF_ENABLED = True
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"mysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST', 'localhost')}/{os.environ.get('DB_NAME')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # Logging
    LOG_LEVEL = logging.WARNING
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = '/var/log/whatsapp-business/app.log'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Meta/WhatsApp API
    META_APP_ID = os.environ.get('META_APP_ID')
    META_REDIRECT_URI = os.environ.get('META_REDIRECT_URI')
    META_PERMISSIONS = 'whatsapp_business_management,business_management'
    META_APP_SECRET = os.environ.get('META_APP_SECRET')
    
    # Platform WhatsApp Business API
    PLATFORM_WABA_ID = os.environ.get('PLATFORM_WABA_ID')
    PLATFORM_PHONE_NUMBER_ID = os.environ.get('PLATFORM_PHONE_NUMBER_ID')
    PLATFORM_ACCESS_TOKEN = os.environ.get('PLATFORM_ACCESS_TOKEN')
    
    # Payment Gateway
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    }