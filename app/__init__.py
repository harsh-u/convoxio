from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
import re
import logging
import sys

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure logging
    logging.basicConfig(
        level=app.config['LOG_LEVEL'],
        format=app.config['LOG_FORMAT'],
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )
    
    # Create logger for the application
    app.logger.setLevel(app.config['LOG_LEVEL'])
    app.logger.info("🚀 Flask application starting up...")
    
    # Enable CORS for React frontend
    CORS(app, supports_credentials=True)
    app.logger.info("✅ CORS enabled for React frontend")

    db.init_app(app)
    app.logger.info("📊 Database initialized")
    
    login_manager.init_app(app)
    login_manager.login_view = 'api.login'
    app.logger.info("🔐 Login manager initialized")

    # Add custom Jinja2 filter for regex
    @app.template_filter('regex_findall')
    def regex_findall_filter(text, pattern):
        return re.findall(pattern, text)

    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    app.logger.info("🌐 Main routes blueprint registered")

    from app.admin_routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)
    app.logger.info("👑 Admin routes blueprint registered")

    # Add request logging middleware
    @app.before_request
    def log_request_info():
        app.logger.info(f"📥 {request.method} {request.url} - IP: {request.remote_addr}")

    @app.after_request
    def log_response_info(response):
        app.logger.info(f"📤 Response: {response.status_code} for {request.method} {request.url}")
        return response

    app.logger.info("✨ Flask application setup complete!")
    return app
