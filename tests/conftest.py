import pytest
from app import create_app
from app.database import db
from app.models import User

@pytest.fixture(scope='module')
def app():
    """
    Fixture to create a Flask app configured for testing
    """
    app = create_app('testing')
    with app.app_context():
        db.create_all()
    return app

@pytest.fixture(scope='module')
def test_client(app):
    """
    Fixture to create a test client for the application
    """
    return app.test_client()

@pytest.fixture(scope='module')
def _db(app):
    """
    Fixture to set up the database for testing
    """
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def test_user(_db):
    """
    Fixture to create a test user for each test function
    """
    user = User(
        full_name='Test User', 
        year=12, 
        maths_class='Test Class',
        key_stage='KS5'
    )
    user.set_password('testpassword')
    
    _db.session.add(user)
    _db.session.commit()
    
    return user