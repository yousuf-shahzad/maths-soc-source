"""
WSGI Entry Point for Production Deployment
==========================================

This module provides the WSGI application object for production deployment
with Gunicorn or other WSGI servers.

Usage:
    gunicorn wsgi:application
    gunicorn --bind 0.0.0.0:8000 wsgi:application
    gunicorn --workers 4 --bind 0.0.0.0:8000 wsgi:application
"""

import os
from app import create_app

# Determine the configuration based on environment
config_name = os.environ.get('FLASK_CONFIG', 'production')

# Create the Flask application
application = create_app(config_name)

if __name__ == "__main__":
    # This allows running directly with Python for testing
    # In production, use: gunicorn wsgi:application
    application.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
