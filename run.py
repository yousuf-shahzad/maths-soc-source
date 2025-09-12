"""
Development Server Entry Point
==============================

This is for local development only. In production, use wsgi.py with Gunicorn.
"""

import os
from app import create_app

# Use development config for local running
app = create_app('development')

if __name__ == '__main__':
    # Only enable debug in development
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)