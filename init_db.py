#!/usr/bin/env python3
"""
Database Initialization Script
=============================

This script initializes the database with default data including schools
and other necessary data for the application to function properly.

Usage:
    python init_db.py

Functions:
    - init_schools(): Add default schools to the database
    - init_all(): Initialize all default data
"""

from app import create_app, db
from app.models import School, User
from flask import current_app


def init_schools():
    """Initialize default schools in the database."""
    print("Initializing schools...")
    
    # Check if schools already exist
    if School.query.count() > 0:
        print(f"Schools already exist in database ({School.query.count()} found)")
        return
    
    default_schools = [
        {
            'name': 'Upton Court Grammar School (UCGS)',
            'email_domain': 'uptoncourtgrammar.org.uk',
            'address': 'Slough, Berkshire SL3 7PR',
        },
    ]
    
    for school_data in default_schools:
        school = School(**school_data)
        db.session.add(school)
        print(f"Added school: {school_data['name']}")
    
    try:
        db.session.commit()
        print(f"Successfully added {len(default_schools)} schools to the database")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding schools: {e}")
        raise


def init_admin_user():
    """Initialize a default admin user (development only)."""
    if current_app.config.get('ENV') == 'production':
        print("Skipping admin user creation in production")
        return
    
    print("Initializing admin user...")
    
    # Check if admin user already exists
    admin_user = User.query.filter_by(is_admin=True).first()
    if admin_user:
        print(f"Admin user already exists: {admin_user.full_name}")
        return
    
    # Create default admin user
    admin = User(
        full_name="Admin User",
        email="admin@ucgs.ac.uk",
        year=13,
        key_stage="KS5",
        maths_class="A-Level",
        user_type="ucgs",
        school_id=1,  # UCGS
        is_admin=True,
        is_competition_participant=False
    )
    admin.set_password("admin123")  # Change this in production!
    
    db.session.add(admin)
    
    try:
        db.session.commit()
        print("Successfully created admin user")
        print("Username: Admin User")
        print("Password: admin123")
        print("Year: 13")
        print("*** REMEMBER TO CHANGE THE PASSWORD! ***")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating admin user: {e}")
        raise


def init_all():
    """Initialize all default data."""
    print("=== Database Initialization ===")
    
    # Create all tables
    print("Creating database tables...")
    db.create_all()
    print("Database tables created")
    
    # Initialize data
    init_schools()
    init_admin_user()
    
    print("=== Initialization Complete ===")


if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        init_all()
