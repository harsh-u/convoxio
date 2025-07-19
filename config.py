import os

class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@localhost/whatsapp_onboarding'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max 16MB file
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # Meta configuration
    META_APP_ID = '2012311039173242'
    META_REDIRECT_URI = 'https://512092dbeee4.ngrok-free.app/onboard/callback'
    META_PERMISSIONS = 'whatsapp_business_management,business_management'
    META_APP_SECRET = '55c57e7dcb4347d90bc6f50f79e307f4'
