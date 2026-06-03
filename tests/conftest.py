import pytest

from app import app as flask_app
from extensions import db


@pytest.fixture(scope="session")
def app():
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret",
        "API_KEYS": ["test-api-key"],
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": "secret",
    })
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()
