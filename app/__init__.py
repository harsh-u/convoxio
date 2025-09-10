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

    # Register API blueprints
    from app.api.auth import auth_api
    from app.api.dashboard import dashboard_api
    from app.api.templates import templates_api
    from app.api.messaging import messaging_api
    from app.api.uploads import uploads_api
    from app.api.analytics import analytics_api
    from app.api.onboarding import onboarding_api
    
    app.register_blueprint(auth_api, url_prefix='/api/auth')
    app.register_blueprint(dashboard_api, url_prefix='/api')
    app.register_blueprint(templates_api, url_prefix='/api')
    app.register_blueprint(messaging_api, url_prefix='/api')
    app.register_blueprint(uploads_api, url_prefix='/api')
    app.register_blueprint(analytics_api, url_prefix='/api')
    app.register_blueprint(onboarding_api, url_prefix='/api')
    app.logger.info("🔗 API blueprints registered")

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
