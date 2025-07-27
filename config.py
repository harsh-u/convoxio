import os

class Config:
    SECRET_KEY = 'your-secret-key-change-in-production'
    # SQLite for quick testing (switch back to MySQL later)
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@localhost/whatsapp_business'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max 16MB file
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # Meta configuration
    META_APP_ID = '2012311039173242'
    META_REDIRECT_URI = 'https://512092dbeee4.ngrok-free.app/onboard/callback'
    META_PERMISSIONS = 'whatsapp_business_management,business_management'
    META_APP_SECRET = '55c57e7dcb4347d90bc6f50f79e307f4'
    
    # Platform WhatsApp Business API (YOUR credentials)
    PLATFORM_WABA_ID = 'your_platform_waba_id'
    PLATFORM_PHONE_NUMBER_ID = 'your_platform_phone_id'
    PLATFORM_ACCESS_TOKEN = 'your_platform_access_token'
    
    # Razorpay configuration
    RAZORPAY_KEY_ID = 'rzp_test_your_key_id'  # Replace with your actual key
    RAZORPAY_KEY_SECRET = 'your_secret_key'   # Replace with your actual secret
    
    # Email configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-email@gmail.com'
    MAIL_PASSWORD = 'your-app-password'
