from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from config import Config

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

    from app.api_routes import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from app.admin_routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    return app
