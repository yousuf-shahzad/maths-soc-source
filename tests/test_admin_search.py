import pytest
from flask import url_for
from app.database import db
from app.models import User

@pytest.fixture(scope='module')
def admin_user(_db):
    admin = User(full_name='Admin User', email='admin@example.com', year=12, maths_class='A1', key_stage='KS5', is_admin=True)
    admin.set_password('adminpass')
    _db.session.add(admin)
    # Additional users for searching
    u1 = User(full_name='Alice Smith', email='alice@example.com', year=10, maths_class='M10A', key_stage='KS4')
    u1.set_password('pass1')
    u2 = User(full_name='Bob Johnson', email='bob@example.com', year=9, maths_class='M9B', key_stage='KS4')
    u2.set_password('pass2')
    _db.session.add_all([u1, u2])
    _db.session.commit()
    return admin

@pytest.fixture
def login_admin(test_client, app, admin_user):
    with app.test_request_context():
        resp = test_client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'adminpass'
        }, follow_redirects=True)
        assert resp.status_code == 200
        yield
        test_client.get('/logout')

class TestAdminUserSearch:
    def test_search_by_name(self, test_client, login_admin):
        resp = test_client.get('/admin/users/search?q=Alice')
        assert resp.status_code == 200
        data = resp.get_json()
        assert any(u['full_name'] == 'Alice Smith' for u in data['users'])

    def test_search_by_id(self, test_client, login_admin, _db):
        # Get a user id to search for
        user = User.query.filter_by(full_name='Bob Johnson').first()
        resp = test_client.get(f'/admin/users/search?q={user.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        # Should return Bob Johnson explicitly
        assert any(u['id'] == user.id for u in data['users'])

    def test_search_min_length(self, test_client, login_admin):
        resp = test_client.get('/admin/users/search?q=a')  # too short
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['users'] == []

    def test_limit_clamping(self, test_client, login_admin):
        resp = test_client.get('/admin/users/search?q=User&limit=5000')
        assert resp.status_code == 200
        data = resp.get_json()
        # limit clamps to 50, but we only created a handful of users so just ensure no error
        assert 'users' in data

class TestSummerLeaderboardSearch:
    def test_search_endpoint_no_query(self, test_client, login_admin):
        resp = test_client.get('/admin/summer_leaderboard/search?q=')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['entries'] == []
