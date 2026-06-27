import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import User


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def create_user(app):
    def _factory(
        username: str,
        role: str = "user",
        rating_score: float = 0.0,
        warnings: int = 0,
        shadow_ban: bool = False,
        is_blocked: bool = False,
        blocked_until=None,
        email: str | None = None,
        password: str = "password",
    ):
        password_hash = generate_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            rating_score=rating_score,
            warnings=warnings,
            shadow_ban=shadow_ban,
            is_blocked=is_blocked,
            blocked_until=blocked_until,
        )
        db.session.add(user)
        db.session.commit()
        return user

    with app.app_context():
        yield _factory


@pytest.fixture()
def login_user(client, create_user):
    def _factory(username: str, role: str = "user", **kwargs):
        password = kwargs.pop("password", "password")
        user = create_user(username=username, role=role, password=password, **kwargs)
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200
        return user

    return _factory
