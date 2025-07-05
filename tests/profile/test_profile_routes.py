import pytest
from flask import url_for
from app.models import User, LeaderboardEntry
from datetime import datetime

def test_profile_route_requires_login(test_client):
    """
    GIVEN an unauthenticated user
    WHEN accessing the profile page
    THEN redirect to login page
    """
    response = test_client.get('/profile/', follow_redirects=True)
    assert response.status_code == 401
    # assert b'Sign In' in response.data

def test_profile_page_renders(test_client, test_user, app, _db):
    """
    GIVEN an authenticated user
    WHEN accessing the profile page
    THEN page renders successfully with user data
    """
    with app.test_request_context():
        # Log in the test user
        test_client.post('/login', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'password': 'testpassword'
        })

        # Create mock leaderboard entry for the test user
        leaderboard_entry = LeaderboardEntry(
            user_id=test_user.id,
            score=100,
            last_updated=datetime.now(),
            key_stage='KS4',
        )

        _db.session.add(leaderboard_entry)
        _db.session.commit()

        # Access profile page
        response = test_client.get('/profile/')
        assert response.status_code == 200
        assert b'Profile' in response.data

def test_change_password_invalid_current_password(test_client, test_user, app):
    """
    GIVEN an authenticated user
    WHEN changing password with incorrect current password
    THEN password change is rejected
    """
    with app.test_request_context():
        # Log in the test user
        test_client.post('/login', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'password': 'testpassword'
        })

        # Attempt to change password with wrong current password
        response = test_client.post('/profile/change_password', data={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid current password' in response.data

def test_change_password_mismatched_new_passwords(test_client, test_user, app):
    """
    GIVEN an authenticated user
    WHEN changing password with mismatched new passwords
    THEN password change is rejected
    """
    with app.test_request_context():
        # Log in the test user
        test_client.post('/login', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'password': 'testpassword'
        })

        # Attempt to change password with mismatched new passwords
        response = test_client.post('/profile/change_password', data={
            'current_password': 'testpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Ensure both new passwords are the same' in response.data

def test_change_password_route(test_client, test_user, app):
    """
    GIVEN an authenticated user
    WHEN changing password with valid data
    THEN password is updated successfully
    """
    with app.test_request_context():
        # Log in the test user
        test_client.post('/login', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'password': 'testpassword'
        })

        # Attempt to change password
        response = test_client.post('/profile/change_password', data={
            'current_password': 'testpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Your password has been updated' in response.data

        # Verify the new password works
        logout_response = test_client.get('/logout')
        login_response = test_client.post('/login', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'password': 'newpassword123'
        }, follow_redirects=True)

        assert b'Sign In' not in login_response.data

def test_delete_account_route(test_client, test_user, _db, app):
    """
    GIVEN an authenticated user
    WHEN deleting their account
    THEN account is removed from the database
    """
    with app.test_request_context():
        # Log in the test user
        test_client.post('/login', data={
            'first_name': 'Test',
            'last_name': 'User',
            'year': '12',
            'password': 'testpassword'
        })

        # Delete account
        response = test_client.get('/profile/delete_account', follow_redirects=True)

        assert response.status_code == 200
        assert b'Your account has been deleted' in response.data

        # Verify user is removed from database
        deleted_user = User.query.filter_by(id=1).first()
        assert deleted_user is None

def test_delete_account_requires_login(test_client):
    """
    GIVEN an unauthenticated user
    WHEN attempting to delete an account
    THEN redirect to login page
    """
    response = test_client.get('/profile/delete_account', follow_redirects=True)
    assert response.status_code == 401
    # assert b'Sign In' in response.data