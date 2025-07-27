from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
import re

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for React frontend
    CORS(app, supports_credentials=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'api.login'

    # Add custom Jinja2 filter for regex
    @app.template_filter('regex_findall')
    def regex_findall_filter(text, pattern):
        return re.findall(pattern, text)

    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.admin_routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    return app
