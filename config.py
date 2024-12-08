import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with common settings"""
    # Secret key with fallback
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    
    # Consistent SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Logging configuration
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() == 'true'

    # Application-specific paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')

    @classmethod
    def is_production(cls):
        """
        Determine if the application is running in production mode
        based on environment variables
        """
        return os.environ.get('FLASK_ENV') == 'production' or \
               os.environ.get('APP_ENVIRONMENT') == 'production' or \
               os.environ.get('ENV') == 'prod'

    @classmethod
    def get_database_uri(cls, database_name=None):
        """
        Dynamically generate database URI with sensible defaults
        Supports different database types and configurations
        """
        # Prioritize environment variable
        if os.environ.get('DATABASE_URL'):
            return os.environ.get('DATABASE_URL')
        
        # Default to PostgreSQL
        db_type = os.environ.get('DATABASE_TYPE', 'postgresql')
        db_username = os.environ.get('DB_USERNAME', 'postgres')
        db_password = os.environ.get('DB_PASSWORD', '')
        db_host = os.environ.get('DB_HOST', 'localhost')
        
        # Use provided database name or fallback to default
        db_name = database_name or os.environ.get('DB_NAME', 'myapp')
        
        if db_type == 'postgresql':
            return f'postgresql://{db_username}:{db_password}@{db_host}/{db_name}'
        elif db_type == 'sqlite':
            return f'sqlite:///{os.path.join(cls.BASE_DIR, f"{db_name}.db")}'
        else:
            raise ValueError(f"Unsupported database type: {db_type}")


class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = Config.get_database_uri('socdb')
    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_HEIGHT = 400


class TestingConfig(Config):
    """Testing-specific configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    # Can be overridden by environment variables
    SQLALCHEMY_DATABASE_URI = Config.get_database_uri('myapp_prod')


# Configuration selector
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

def get_config(config_name='development'):
    """
    Retrieve the appropriate configuration class
    
    Args:
        config_name (str): Name of the configuration ('development', 'testing', 'production')
    
    Returns:
        Config: Configuration class for the specified environment
    """
    if Config.is_production() or config_name == 'production':
        return ProductionConfig
    elif os.environ.get('FLASK_ENV') == 'testing' or os.environ.get('APP_ENVIRONMENT') == 'testing' or config_name == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig