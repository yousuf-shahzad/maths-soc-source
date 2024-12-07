from flask import Flask
import logging
from flask_login import LoginManager
from app.models import User
from app.database import db
from flask_migrate import Migrate
from config import Config, TestingConfig
from flask_ckeditor import CKEditor

login_manager = LoginManager()
migrate = Migrate()
ckeditor = CKEditor()


def create_app(config_type='development'):
    """
    Application factory with support for different configuration types

    Args:
        config_type (str): Configuration type - 'development', 'testing', or 'production'
    """
    # Choose the appropriate configuration
    config_mapping = {
        'development': Config,
        'testing': TestingConfig,
        # 'production': ProductionConfig
    }

    # Default to development if an unknown config is passed
    config_class = config_mapping.get(config_type, Config)

    # Create the Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.logger.setLevel(logging.INFO)

    # Initialize extensions
    ckeditor.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Setup database migrations
    migrate.init_app(app, db, render_as_batch=True)

    # Import blueprints (do this inside the function to avoid circular imports)
    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.profile import bp as profile_bp
    from app.admin import bp as admin_bp

    # Register blueprints with URL prefixes
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(admin_bp)

    return app
