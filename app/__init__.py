from flask import Flask
import logging
from flask_login import LoginManager
from app.models import User
from app.database import db
from flask_migrate import Migrate
from config import Config
from flask_ckeditor import CKEditor

login_manager = LoginManager()
migrate = Migrate()
ckeditor = CKEditor()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.logger.setLevel(logging.INFO)
    
    ckeditor.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    migrate.init_app(app, db, render_as_batch=True)
    
    # Import blueprints
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