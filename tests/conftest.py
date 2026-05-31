import os

import pytest

from app import create_app
from extensions import db


def pytest_configure():
    os.environ["FLASK_ENV"] = "testing"
    os.environ["JWT_SECRET_KEY"] = "test-secret"
    os.environ["API_KEYS"] = "test-api-key"


@pytest.fixture(scope="session")
def app():
    app = create_app()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()
