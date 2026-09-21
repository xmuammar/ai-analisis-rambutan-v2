from typing import ClassVar

import pytest

from app import create_app, db


@pytest.fixture()
def app(tmp_path):
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test"
        WTF_CSRF_ENABLED = False
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.sqlite3'}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        UPLOAD_FOLDER = tmp_path / "uploads"
        ALLOWED_IMAGE_EXTENSIONS: ClassVar[set[str]] = {"jpg", "jpeg", "png", "webp"}
        AUTO_CREATE_SCHEMA = True

    application = create_app(TestConfig)
    with application.app_context():
        from app.models import User

        user = User(username="tester")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
    yield application
    with application.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    client = app.test_client()
    client.post("/auth/login", data={"username": "tester", "password": "password123"})
    return client
