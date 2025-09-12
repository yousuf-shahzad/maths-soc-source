import logging
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_ckeditor import CKEditor
from app.database import db
from flask import render_template
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import text

# Import configuration
from config import get_config

# Initialize extensions
login_manager = LoginManager()
migrate = Migrate()
ckeditor = CKEditor()


def create_app(config_name="development"):
    """
    Application factory with improved configuration management

    Args:
        config_name (str): Configuration environment ('development', 'testing', 'production')
    """
    # Get the appropriate configuration
    config_class = get_config(config_name)

    # Create the Flask app
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_class)

    # Configure logging
    configure_logging(app)

    # Initialize extensions
    initialize_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Health and readiness endpoints (no auth, no DB by default)
    @app.route('/healthz')
    def healthz():
        return {"status": "ok"}, 200

    @app.route('/readyz')
    def readyz():
        # Lightweight DB check; won't raise if DB temporarily down
        try:
            db.session.execute(text('SELECT 1'))
            return {"status": "ready"}, 200
        except Exception:
            return {"status": "degraded"}, 503

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500) 
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    # Content Security Policy (CSP)
    # Note: CKEditor 4 and some math libraries may require 'unsafe-eval'.
    # In production consider serving assets locally and removing 'unsafe-eval' if possible.
    is_dev_like = bool(app.config.get('DEBUG') or app.config.get('TESTING'))
    allow_unsafe_eval = bool(app.config.get('CSP_ALLOW_UNSAFE_EVAL', False) or is_dev_like)

    script_src_common = [
        "'self'",
        "'unsafe-inline'",
        # Third-party CDNs used by the app/UI
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
        "https://polyfill.io",
        "https://unpkg.com",
        "https://cdn.ckeditor.com",
        # Some pages may include analytics from Cloudflare (safe to keep blocked if unused)
        "https://static.cloudflareinsights.com",
    ]

    # CKEditor 4 and some math libs (e.g. MathLive) use eval/new Function
    if allow_unsafe_eval:
        script_src_common.append("'unsafe-eval'")
    else:
        # If you must allow it in prod due to CKEditor 4, uncomment next line
        # script_src_common.append("'unsafe-eval'")
        pass

    csp = {
        'default-src': ["'self'"],
        'base-uri': ["'self'"],
        'object-src': ["'none'"],
        # Be explicit for element/attr directives
        'script-src': script_src_common,
        'script-src-elem': script_src_common,
        'script-src-attr': ["'self'", "'unsafe-inline'"],
        'style-src': [
            "'self'", "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "https://fonts.googleapis.com",
            "https://unpkg.com",
        ],
        'font-src': [
            "'self'",
            "https://fonts.gstatic.com",
            "https://cdnjs.cloudflare.com",
            "https://unpkg.com",
            "data:",
        ],
        'img-src': ["'self'", "data:", "blob:"],
        'connect-src': [
            "'self'",
            "https://cdnjs.cloudflare.com",
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
        ],
        'frame-ancestors': ["'self'"],
        'worker-src': ["'self'", "blob:"],
        'media-src': ["'self'", "data:", "blob:"],
    }

    Talisman(
        app,
        force_https=not (app.config.get('DEBUG') or app.config.get('TESTING')),
        strict_transport_security=True,
        content_security_policy=csp,
    )
    
    return app




def configure_logging(app):
    """Configure application logging"""
    if app.config.get("LOG_TO_STDOUT"):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
    else:
        # Configure file-based logging if needed
        logging.basicConfig(
            filename="app.log",
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def initialize_extensions(app):
    """Initialize Flask extensions"""
    ckeditor.init_app(app)
    db.init_app(app)

    login_manager.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    # User loader for Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def register_blueprints(app):
    """Register application blueprints"""
    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.profile import bp as profile_bp
    from app.admin import bp as admin_bp
    from app.math_api import math_api

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(admin_bp)
    app.register_blueprint(math_api)