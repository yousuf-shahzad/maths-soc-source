from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.models import User
from app.database import db
from flask_migrate import Migrate
from config import Config

login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(user_id):
        # Return the user object for the given user_id
        return User.query.get(int(user_id))

    migrate.init_app(app, db)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)


    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp)

    return app
