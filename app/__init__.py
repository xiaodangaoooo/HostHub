from flask import Flask
from flask_login import LoginManager
from config import Config
from app.utils.db import close_db
from app.models.user import User

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    login_manager.init_app(app)
    
    # Set up login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Register database teardown
    app.teardown_appcontext(close_db)
    
    # Register blueprints
    from app.routes import main_bp, auth_bp, host_bp, traveler_bp, settings_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(host_bp, url_prefix='/host')
    app.register_blueprint(traveler_bp, url_prefix='/traveler')
    app.register_blueprint(settings_bp)


    return app