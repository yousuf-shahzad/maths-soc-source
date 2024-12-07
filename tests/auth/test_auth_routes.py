import pytest
from flask import url_for
from werkzeug.security import generate_password_hash

def test_login_page_renders(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b'Sign In' in response.data

def test_login_success(test_client, test_user, app):
    """
    GIVEN a registered user
    WHEN valid credentials are submitted
    THEN user is logged in and redirected to index
    """
    with app.test_request_context():
        response = test_client.post('/login', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'password': 'testpassword',
            'remember_me': 'y'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Sign In' not in response.data  # Implies successful login

        response = test_client.get('/logout', follow_redirects=True) # Clean up

def test_login_invalid_credentials(test_client, test_user, app):
    """
    GIVEN a registered user
    WHEN invalid credentials are submitted
    THEN login fails with an error message
    """
    with app.test_request_context():
        response = test_client.post('/login', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid name or password' in response.data

def test_login_nonexistent_user(test_client, app):
    """
    GIVEN no registered users
    WHEN login is attempted with non-existent credentials
    THEN login fails with an error message
    """
    with app.test_request_context():
        response = test_client.post('/login', data={
            'first_name': 'Nonexistent',
            'last_name': 'User',
            'year': '12',
            'password': 'somepassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid name or password' in response.data

def test_register_new_user(test_client, _db, app):
    """
    GIVEN a Flask application
    WHEN a new user registers with valid data
    THEN user is created and redirected to login
    """
    with app.test_request_context():
        response = test_client.post('/register', data={
            'first_name': 'New',
            'last_name': 'Student',
            'year': '10',
            'maths_class': 'Math10A',
            'password': 'validpassword123',
            'password2': 'validpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Congratulations, you are now a registered user!' in response.data
        
        # Verify user was actually created
        from app.models import User
        user = User.query.filter_by(full_name='New Student').first()
        assert user is not None
        assert user.year == 10
        assert user.key_stage == 'KS4'
        assert user.maths_class == 'Math10A'

def test_register_duplicate_user(test_client, test_user, app):
    """
    GIVEN an existing user
    WHEN attempting to register with same name and year
    THEN registration is prevented
    """
    with app.test_request_context():
        response = test_client.post('/register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'maths_class': 'Test Class',
            'password': 'somepassword',
            'password2': 'somepassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'A user with this name and year already exists' in response.data

def test_register_profanity_check(test_client, app):
    """
    GIVEN a registration attempt
    WHEN name contains profanity
    THEN registration is prevented
    """
    with app.test_request_context():
        response = test_client.post('/register', data={
            'first_name': 'Fuck',
            'last_name': 'Swear',
            'year': '9',
            'maths_class': 'Math9B',
            'password': 'validpassword123',
            'password2': 'validpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Unauthorized content detected in your name' in response.data

def test_register_whitespace_in_name(test_client, app):
    """
    GIVEN a registration attempt
    WHEN name contains whitespace
    THEN registration is prevented
    """
    with app.test_request_context():
        response = test_client.post('/register', data={
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'year': '9',
            'maths_class': 'Math9B',
            'password': 'validpassword123',
            'password2': 'validpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Please remove any whitespace from your name' in response.data

def test_logout(test_client, test_user, app):
    """
    GIVEN a logged-in user
    WHEN logout is called
    THEN user is logged out and redirected to index
    """
    # First, log in the user
    with app.test_request_context():
        test_client.post('/login', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'password': 'testpassword'
        })

        # Then logout
        response = test_client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        # Could add additional checks to verify logout state if needed