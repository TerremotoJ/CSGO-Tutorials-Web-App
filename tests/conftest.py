"""Fixtures: each test gets a new app on its own temporary SQLite file, seeded like a first start."""
import os
import tempfile

import pytest

# config.py reads these at import time; the tests never touch instance/app.db
os.environ['SECRET_KEY'] = 'test-only-secret'
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.join(tempfile.mkdtemp(), 'unused.db')

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from config import Config  # noqa: E402


@pytest.fixture
def make_app(tmp_path):
    """Returns a factory: make_app(db_path=None, **settings) builds an app on a temporary database."""
    apps = []

    def _make(db_path=None, **settings):
        class TestConfig(Config):
            TESTING = True
            WTF_CSRF_ENABLED = False
            SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(db_path or tmp_path / 'test.db')

        for name, value in settings.items():
            setattr(TestConfig, name, value)
        app = create_app(TestConfig)
        apps.append(app)
        return app

    yield _make

    for app in apps:
        with app.app_context():
            db.engine.dispose()


@pytest.fixture
def app(make_app):
    return make_app()


@pytest.fixture
def client_for(app):
    """Returns a factory: client_for(None) is logged out, 'anonymous' gets the automatic
    Anonymous-Account, any other value logs in that seeded username (password 'password')."""
    def _client(username=None):
        client = app.test_client()
        if username == 'anonymous':
            client.get('/')
        elif username:
            response = client.post('/login', data={'username': username, 'password': 'password'})
            assert response.status_code == 302 and response.headers['Location'] == '/'
        return client

    return _client
